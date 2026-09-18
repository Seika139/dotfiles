package main

import (
	"encoding/json"
	"errors"
	"io"
	"math"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"
)

func TestTimeoutOverflowAndEmptyModelFields(t *testing.T) {
	if _, _, _, _, _, _, _, err := parse([]string{"--timeout", "999999999999"}); err == nil {
		t.Fatal("duration overflow accepted")
	}
	maxSeconds := float64(time.Duration(1<<63-1)) / float64(time.Second)
	if !validTimeout(maxSeconds) || validTimeout(math.Nextafter(maxSeconds, math.Inf(1))) {
		t.Fatalf("timeout boundary validation failed: max=%v", maxSeconds)
	}
	_, _, _, _, timeout, _, _, err := parse([]string{"--timeout", "1"})
	if timeout != 1 || err == nil {
		t.Fatalf("timeout was not parsed before key input: timeout=%v err=%v", timeout, err)
	}
	models := []model{}
	count := 0
	truncated := false
	b, err := json.Marshal(modelsEndpoint{Outcome: "endpoint_accessible", Models: &models, ModelCount: &count, ModelsTruncated: &truncated})
	if err != nil || !strings.Contains(string(b), `"models":[]`) || !strings.Contains(string(b), `"model_count":0`) || !strings.Contains(string(b), `"models_truncated":false`) {
		t.Fatalf("missing empty model fields: %s", b)
	}
}

func TestVerbosityControlsDetailedFields(t *testing.T) {
	models := []model{{ID: "gpt-test"}}
	count := 1
	truncated := false
	out := result{
		SchemaVersion: 3,
		Status:        "endpoint_accessible",
		ModelsEndpoint: modelsEndpoint{
			Outcome:         "endpoint_accessible",
			Status:          http.StatusOK,
			Headers:         map[string]string{"x-request-id": "r"},
			Models:          &models,
			ModelCount:      &count,
			ModelsTruncated: &truncated,
		},
		ModelEndpoint: &endpoint{Outcome: "endpoint_accessible", Status: http.StatusOK, Headers: map[string]string{"x-request-id": "r"}},
	}
	applyVerbosity(&out, false)
	b, err := json.Marshal(out)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(b), `"headers"`) || strings.Contains(string(b), `"models"`) || strings.Contains(string(b), `"models_truncated"`) {
		t.Fatalf("default output contains verbose fields: %s", b)
	}
	if !strings.Contains(string(b), `"model_count":1`) {
		t.Fatalf("default output lost model count: %s", b)
	}

	// Rebuild the detailed fields because the compacting operation intentionally
	// removes them from the result in place.
	out.ModelsEndpoint.Headers = map[string]string{"x-request-id": "r"}
	out.ModelsEndpoint.Models = &models
	out.ModelsEndpoint.ModelsTruncated = &truncated
	out.ModelEndpoint.Headers = map[string]string{"x-request-id": "r"}
	applyVerbosity(&out, true)
	b, err = json.Marshal(out)
	if err != nil {
		t.Fatal(err)
	}
	for _, field := range []string{`"headers"`, `"models"`, `"models_truncated"`} {
		if !strings.Contains(string(b), field) {
			t.Fatalf("verbose output missing %s: %s", field, b)
		}
	}
}

func TestSafeHeadersAndError(t *testing.T) {
	h := http.Header{
		"X-Request-Id":               {"r"},
		"X-Ratelimit-Limit-Requests": {"10"},
		"X-Ratelimit-Authorization":  {"Bearer secret"},
		"X-Secret":                   {"s"},
	}
	got := safeHeaders(h)
	if len(got) != 2 || got["x-request-id"] != "r" || got["x-ratelimit-limit-requests"] != "10" {
		t.Fatalf("unexpected safe headers: %#v", got)
	}
	encoded, _ := json.Marshal(got)
	if strings.Contains(string(encoded), "Authorization") || strings.Contains(string(encoded), "secret") {
		t.Fatalf("sensitive header leaked: %s", encoded)
	}
	typ, code := errorFields([]byte(`{"error":{"type":"x","code":"c","message":"secret"}}`))
	if typ != "x" || code != "c" {
		t.Fatal()
	}
}
func TestHTTPAndRedirect(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if got := r.Header.Get("Authorization"); got != "Bearer k" {
			t.Errorf("authorization = %q", got)
		}
		if r.URL.Path == "/redirect" {
			http.Redirect(w, r, "/ok", 302)
			return
		}
		w.Header().Set("X-Request-Id", "r")
		w.Write([]byte(`{"data":[]}`))
	}))
	defer srv.Close()
	c := &http.Client{CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	e, code, _, _, _ := request(c, "k", "", "", srv.URL+"/ok")
	if code != 0 || e.Outcome != "endpoint_accessible" {
		t.Fatal(e, code)
	}
	e, code, _, _, _ = request(c, "k", "", "", srv.URL+"/redirect")
	if code != 13 || e.Status != 302 {
		t.Fatal(e, code)
	}
}

func TestUnauthorizedResponseDoesNotExposeMessage(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusUnauthorized)
		_, _ = w.Write([]byte(`{"error":{"type":"invalid_api_key","code":"invalid_api_key","message":"do not print this"}}`))
	}))
	defer srv.Close()
	c := &http.Client{}
	e, code, body, tooLarge, readErr := request(c, "secret-key", "", "", srv.URL)
	if code != 10 || e.Outcome != "rejected" || body != nil || tooLarge || readErr || e.ErrorType != "invalid_api_key" || e.ErrorCode != "invalid_api_key" {
		t.Fatalf("unexpected unauthorized result: %+v code=%d body=%v too_large=%v read_err=%v", e, code, body, tooLarge, readErr)
	}
	encoded, _ := json.Marshal(e)
	if strings.Contains(string(encoded), "do not print this") || strings.Contains(string(encoded), "secret-key") {
		t.Fatalf("secret error output: %s", encoded)
	}
}
func TestSummarize(t *testing.T) {
	var e modelsEndpoint
	s := []byte(`{"data":[{"id":"a","owned_by":"o","created":true,"shutdown_date":2,"message":"x"}]}`)
	summarize(&e, s)
	if *e.ModelCount != 1 || len(*e.Models) != 1 || (*e.Models)[0].ID != "a" || (*e.Models)[0].Created != true || (*e.Models)[0].ShutdownDate != float64(2) {
		t.Fatal(e)
	}
	summarize(&e, []byte(`{"data":[{"id":"b","created":[],"shutdown_date":{}}]}`))
	if (*e.Models)[0].Created != nil || (*e.Models)[0].ShutdownDate != nil {
		t.Fatalf("invalid metadata values were retained: %+v", *e.Models)
	}
}

func TestInvalidMetadataKeepsEndpointAccessibleShape(t *testing.T) {
	e := modelsEndpoint{Outcome: "endpoint_accessible", Status: http.StatusOK}
	summarize(&e, []byte(`{"data":`))
	if e.Outcome != "endpoint_accessible" || !e.MetadataUnavailable || e.ModelCount != nil || e.Models != nil || e.ModelsTruncated != nil {
		t.Fatalf("unexpected metadata result: %+v", e)
	}
	b, err := json.Marshal(e)
	if err != nil || strings.Contains(string(b), `"models"`) || strings.Contains(string(b), `"model_count"`) || strings.Contains(string(b), `"models_truncated"`) || !strings.Contains(string(b), `"metadata_unavailable":true`) {
		t.Fatalf("missing metadata fields: %s", b)
	}
}

func TestUnavailableMetadataShapes(t *testing.T) {
	for _, body := range []string{`{}`, `{"data":null}`, `{"data":{}}`, `{"data": [}`, `{"data":[1]}`, `{"data":[{}]}`, `{"data":[null]}`, `{"data":[{"id":"ok"},{}]}`, `{"data":[{"id":""}]}`} {
		var e modelsEndpoint
		summarize(&e, []byte(body))
		if !e.MetadataUnavailable || e.ModelCount != nil || e.Models != nil || e.ModelsTruncated != nil {
			t.Fatalf("metadata shape was presented as known for %s: %+v", body, e)
		}
		for _, verbose := range []bool{false, true} {
			out := result{SchemaVersion: 3, ModelsEndpoint: e}
			applyVerbosity(&out, verbose)
			encoded, _ := json.Marshal(out)
			if strings.Contains(string(encoded), `"models"`) || strings.Contains(string(encoded), `"model_count"`) || strings.Contains(string(encoded), `"models_truncated"`) {
				t.Fatalf("unknown metadata fields were emitted (verbose=%v): %s", verbose, encoded)
			}
		}
	}
	large := strings.Repeat("x", maxBody+1)
	var e modelsEndpoint
	markMetadataUnavailable(&e)
	for _, verbose := range []bool{false, true} {
		out := result{SchemaVersion: 3, ModelsEndpoint: e}
		applyVerbosity(&out, verbose)
		encoded, _ := json.Marshal(out)
		if !out.ModelsEndpoint.MetadataUnavailable || strings.Contains(string(encoded), `"models"`) || strings.Contains(string(encoded), `"model_count"`) {
			t.Fatalf("large body metadata was emitted (verbose=%v, body=%d): %s", verbose, len(large), encoded)
		}
	}
}

func TestReadBodyReportsOversize(t *testing.T) {
	body, tooLarge, readErr := readBody(io.NopCloser(strings.NewReader(strings.Repeat("x", maxBody+1))))
	if !tooLarge || readErr || len(body) != maxBody {
		t.Fatalf("unexpected body limit result: len=%d too_large=%v read_err=%v", len(body), tooLarge, readErr)
	}
}

type failingReadCloser struct{}

func (failingReadCloser) Read([]byte) (int, error) { return 0, errors.New("body read failed") }
func (failingReadCloser) Close() error             { return nil }

func TestHTTP200BodyReadErrorLeavesMetadataUnavailable(t *testing.T) {
	client := &http.Client{Transport: roundTripFunc(func(*http.Request) (*http.Response, error) {
		return &http.Response{
			StatusCode: http.StatusOK,
			Header:     make(http.Header),
			Body:       failingReadCloser{},
		}, nil
	})}
	e, code, body, tooLarge, readErr := request(client, "k", "", "", "https://example.invalid/v1/models")
	if code != 0 || e.Outcome != "endpoint_accessible" || body != nil || tooLarge || !readErr {
		t.Fatalf("unexpected read-error response: %+v code=%d body=%v too_large=%v read_err=%v", e, code, body, tooLarge, readErr)
	}
	metadata := modelsResult(e, body, tooLarge, readErr)
	if !metadata.MetadataUnavailable || metadata.Models != nil || metadata.ModelCount != nil || metadata.ModelsTruncated != nil {
		t.Fatalf("read-error metadata was not unavailable: %+v", metadata)
	}
}

func TestRunHTTP200BodyReadErrorOutputAndExitCode(t *testing.T) {
	oldFactory := httpClientFactory
	oldStdin, oldStdout := os.Stdin, os.Stdout
	defer func() {
		httpClientFactory = oldFactory
		os.Stdin, os.Stdout = oldStdin, oldStdout
	}()
	httpClientFactory = func(time.Duration) *http.Client {
		return &http.Client{Transport: roundTripFunc(func(*http.Request) (*http.Response, error) {
			return &http.Response{StatusCode: http.StatusOK, Header: make(http.Header), Body: failingReadCloser{}}, nil
		})}
	}
	inR, inW, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	defer inR.Close()
	if _, err := inW.WriteString("test-key\n"); err != nil {
		t.Fatal(err)
	}
	if err := inW.Close(); err != nil {
		t.Fatal(err)
	}
	outR, outW, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	defer outR.Close()
	os.Stdin, os.Stdout = inR, outW
	exitCode := run([]string{"--api-key-stdin"})
	if err := outW.Close(); err != nil {
		t.Fatal(err)
	}
	output, err := io.ReadAll(outR)
	if err != nil {
		t.Fatal(err)
	}
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d: %s", exitCode, output)
	}
	var got struct {
		SchemaVersion  int    `json:"schema_version"`
		Status         string `json:"status"`
		ModelsEndpoint struct {
			Outcome             string          `json:"outcome"`
			MetadataUnavailable bool            `json:"metadata_unavailable"`
			Models              json.RawMessage `json:"models"`
			ModelCount          json.RawMessage `json:"model_count"`
			ModelsTruncated     json.RawMessage `json:"models_truncated"`
		} `json:"models_endpoint"`
	}
	if err := json.Unmarshal(output, &got); err != nil {
		t.Fatalf("invalid JSON output: %v: %s", err, output)
	}
	if got.SchemaVersion != 3 || got.Status != "endpoint_accessible" || got.ModelsEndpoint.Outcome != "endpoint_accessible" || !got.ModelsEndpoint.MetadataUnavailable {
		t.Fatalf("unexpected output: %s", output)
	}
	for name, value := range map[string]json.RawMessage{"models": got.ModelsEndpoint.Models, "model_count": got.ModelsEndpoint.ModelCount, "models_truncated": got.ModelsEndpoint.ModelsTruncated} {
		if value != nil {
			t.Errorf("unexpected %s field: %s", name, value)
		}
	}
}

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestStdinKeyLengthBoundary(t *testing.T) {
	for _, input := range []string{strings.Repeat("k", 4096), strings.Repeat("k", 4096) + "\n"} {
		key, err := readStdinKey(strings.NewReader(input))
		if err != nil || len(key) != 4096 {
			t.Fatalf("4096-byte key rejected: len=%d err=%v", len(key), err)
		}
	}
	if _, err := readStdinKey(strings.NewReader(strings.Repeat("k", 4097))); err == nil {
		t.Fatal("4097-byte key accepted")
	}
}

func TestNonModelEndpointsDoNotExposeModelFields(t *testing.T) {
	b, err := json.Marshal(endpoint{Outcome: "rejected", Status: 401})
	if err != nil || strings.Contains(string(b), "models") {
		t.Fatalf("unexpected model fields: %s", b)
	}
	b, err = json.Marshal(modelsEndpoint{Outcome: "rejected", Status: 401})
	if err != nil || strings.Contains(string(b), "models") {
		t.Fatalf("unexpected model fields: %s", b)
	}
}

func TestCleanEnvironmentRequiresExactAllowlist(t *testing.T) {
	if !cleanEnvironment([]string{cleanEnvMarker + "=1"}) {
		t.Fatal("marker-only environment was rejected")
	}
	if cleanEnvironment([]string{cleanEnvMarker + "=1", "GODEBUG=http2debug=2"}) {
		t.Fatal("GODEBUG was accepted with clean marker")
	}
	if cleanEnvironment([]string{cleanEnvMarker + "=1", "OPENAI_API_KEY=secret"}) {
		t.Fatal("API key was accepted with clean marker")
	}
}
func TestNoSecretOutput(t *testing.T) {
	var b strings.Builder
	_ = io.Writer(&b)
	x := map[string]any{"schema_version": 3, "status": "input_error", "error": "invalid input"}
	raw, _ := json.Marshal(x)
	if strings.Contains(string(raw), "secret") {
		t.Fatal()
	}
}

func TestIdentityMetadataNormalAndVerbose(t *testing.T) {
	body := []byte(`{"id":"user_1","object":"user","created":1787896772,"name":"Ada","email":"ada@example.com","orgs":{"object":"list","data":[{"id":"org_1","name":"Org","title":"Org title","created":1705469715,"role":"reader","settings":{"disable_user_api_keys":false},"projects":{"object":"list","data":[]}}]}}`)
	identity, unavailable := identityMetadata(endpoint{Outcome: "endpoint_accessible", Status: 200}, body, false, false, false)
	if unavailable || identity["created"] != "2026-08-28T05:59:32Z" || identity["name"] != "Ada" {
		t.Fatalf("unexpected normal identity: %#v unavailable=%v", identity, unavailable)
	}
	orgs := identity["orgs"].([]map[string]any)
	if len(orgs) != 1 || orgs[0]["created"] != "2024-01-17T05:35:15Z" || orgs[0]["title"] != "Org title" {
		t.Fatalf("unexpected normal org: %#v", orgs)
	}
	if _, ok := identity["email"]; ok {
		t.Fatal("normal identity exposed email")
	}
	identity, unavailable = identityMetadata(endpoint{Outcome: "endpoint_accessible", Status: 200}, body, false, false, true)
	if unavailable || identity["created_unix"] != int64(1787896772) || identity["email"] != "ada@example.com" {
		t.Fatalf("unexpected verbose identity: %#v unavailable=%v", identity, unavailable)
	}
	verboseOrgs := identity["orgs"].([]map[string]any)
	if verboseOrgs[0]["created_unix"] != int64(1705469715) || verboseOrgs[0]["role"] != "reader" {
		t.Fatalf("unexpected verbose org: %#v", verboseOrgs)
	}
}

func TestIdentityEmptyOrganizations(t *testing.T) {
	identity, unavailable := identityMetadata(endpoint{Outcome: "endpoint_accessible", Status: 200}, []byte(`{"id":"user_1","created":1,"name":"User","orgs":{"data":[]}}`), false, false, false)
	if unavailable {
		t.Fatal("empty organizations marked unavailable")
	}
	orgs, ok := identity["orgs"].([]map[string]any)
	if !ok || orgs == nil || len(orgs) != 0 {
		t.Fatalf("empty organizations were not retained: %#v", identity)
	}
}

func TestIdentityMetadataUnavailable(t *testing.T) {
	for _, tc := range []struct {
		name      string
		body      []byte
		tooLarge  bool
		readError bool
	}{
		{name: "invalid-json", body: []byte(`{"id":`)},
		{name: "too-large", body: []byte(`{}`), tooLarge: true},
		{name: "read-error", body: nil, readError: true},
	} {
		identity, unavailable := identityMetadata(endpoint{Outcome: "endpoint_accessible", Status: 200}, tc.body, tc.tooLarge, tc.readError, false)
		if !unavailable || identity != nil && len(identity) == 0 {
			t.Fatalf("%s: identity=%#v unavailable=%v", tc.name, identity, unavailable)
		}
	}
	for _, body := range []string{
		`{"id":"u","created":1,"name":"n","orgs":{"data":[{"id":"o","name":"n"}]}}`,
		`{"id":"u","created":1,"orgs":{"data":[]}}`,
	} {
		identity, unavailable := identityMetadata(endpoint{Outcome: "endpoint_accessible", Status: 200}, []byte(body), false, false, false)
		if !unavailable || identity != nil {
			t.Fatalf("invalid required metadata was partially emitted: %#v unavailable=%v", identity, unavailable)
		}
	}
}

func TestIdentityVerboseNestedFieldsAreRebuilt(t *testing.T) {
	body := []byte(`{"id":"u","created":1,"name":"n","amr":["pwd",{"secret":"x"}],"tenants":[{"secret":"x"}],"orgs":{"data":[{"id":"o","name":"n","title":"t","settings":{"disable_user_api_keys":false,"secret":"x"},"projects":{"data":[{"id":"p","secret":"x"}]}}]}}`)
	identity, unavailable := identityMetadata(endpoint{Outcome: "endpoint_accessible", Status: 200}, body, false, false, true)
	if unavailable {
		t.Fatal("valid identity was marked unavailable")
	}
	encoded, err := json.Marshal(identity)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(encoded), "secret") || strings.Contains(string(encoded), "tenants") || strings.Contains(string(encoded), "projects") || strings.Contains(string(encoded), "amr") {
		t.Fatalf("unapproved nested fields leaked: %s", encoded)
	}
	orgs := identity["orgs"].([]map[string]any)
	settings := orgs[0]["settings"].(map[string]any)
	if settings["disable_user_api_keys"] != false {
		t.Fatalf("approved setting missing: %#v", settings)
	}
}

func TestIdentityRequestMethodAndPath(t *testing.T) {
	client := &http.Client{Transport: roundTripFunc(func(r *http.Request) (*http.Response, error) {
		if r.Method != http.MethodGet || r.URL.Path != "/v1/me" {
			t.Fatalf("unexpected identity request: %s %s", r.Method, r.URL.Path)
		}
		if r.Header.Get("Authorization") != "Bearer k" {
			t.Fatalf("authorization = %q", r.Header.Get("Authorization"))
		}
		return &http.Response{StatusCode: http.StatusOK, Header: make(http.Header), Body: io.NopCloser(strings.NewReader(`{"id":"u","created":1,"name":"User","orgs":{"data":[]}}`))}, nil
	})}
	e, code, body, tooLarge, readErr := request(client, "k", "", "", identityURL)
	if code != 0 || e.Outcome != "endpoint_accessible" || tooLarge || readErr {
		t.Fatalf("unexpected identity request result: %+v code=%d", e, code)
	}
	if identity, unavailable := identityMetadata(e, body, tooLarge, readErr, false); unavailable || identity["id"] != "u" {
		t.Fatalf("unexpected identity metadata: %#v unavailable=%v", identity, unavailable)
	}
}

func TestRunIdentityIntegration(t *testing.T) {
	oldFactory := httpClientFactory
	oldStdin, oldStdout := os.Stdin, os.Stdout
	defer func() {
		httpClientFactory = oldFactory
		os.Stdin, os.Stdout = oldStdin, oldStdout
	}()

	runCase := func(t *testing.T, verbose bool, body string) (int, []byte, int) {
		t.Helper()
		calls := 0
		httpClientFactory = func(time.Duration) *http.Client {
			return &http.Client{Transport: roundTripFunc(func(r *http.Request) (*http.Response, error) {
				calls++
				if calls != 1 || r.Method != http.MethodGet || r.URL.String() != identityURL {
					t.Errorf("unexpected identity call #%d: %s %s", calls, r.Method, r.URL.String())
				}
				return &http.Response{StatusCode: http.StatusOK, Header: make(http.Header), Body: io.NopCloser(strings.NewReader(body))}, nil
			})}
		}
		inR, inW, err := os.Pipe()
		if err != nil {
			t.Fatal(err)
		}
		if _, err := inW.WriteString("test-key\n"); err != nil {
			t.Fatal(err)
		}
		_ = inW.Close()
		outR, outW, err := os.Pipe()
		if err != nil {
			t.Fatal(err)
		}
		os.Stdin, os.Stdout = inR, outW
		args := []string{"identity", "--api-key-stdin"}
		if verbose {
			args = append(args, "--verbose")
		}
		code := run(args)
		_ = outW.Close()
		output, err := io.ReadAll(outR)
		_ = inR.Close()
		_ = outR.Close()
		if err != nil {
			t.Fatal(err)
		}
		return code, output, calls
	}

	body := `{"id":"u","created":1,"name":"n","email":"e@example.com","orgs":{"data":[]}}`
	code, output, calls := runCase(t, false, body)
	if code != 0 || calls != 1 {
		t.Fatalf("normal identity run failed: code=%d calls=%d output=%s", code, calls, output)
	}
	var normal identityResult
	if err := json.Unmarshal(output, &normal); err != nil {
		t.Fatal(err)
	}
	if normal.SchemaVersion != 1 || normal.Schema != "openai-key-check/identity" || normal.Identity["created"] != "1970-01-01T00:00:01Z" || normal.IdentityMetadataUnavailable {
		t.Fatalf("unexpected normal identity output: %s", output)
	}
	if _, ok := normal.Identity["email"]; ok {
		t.Fatalf("normal output contains email: %s", output)
	}

	code, output, calls = runCase(t, true, body)
	if code != 0 || calls != 1 {
		t.Fatalf("verbose identity run failed: code=%d calls=%d output=%s", code, calls, output)
	}
	var verbose identityResult
	if err := json.Unmarshal(output, &verbose); err != nil {
		t.Fatal(err)
	}
	if verbose.Identity["created_unix"] != float64(1) || verbose.Identity["email"] != "e@example.com" {
		t.Fatalf("unexpected verbose identity output: %s", output)
	}

	code, output, calls = runCase(t, false, `{"id":`)
	if code != 0 || calls != 1 {
		t.Fatalf("malformed identity run failed: code=%d calls=%d output=%s", code, calls, output)
	}
	var malformed identityResult
	if err := json.Unmarshal(output, &malformed); err != nil {
		t.Fatal(err)
	}
	if !malformed.IdentityMetadataUnavailable || malformed.Identity != nil || malformed.IdentityEndpoint.Outcome != "endpoint_accessible" {
		t.Fatalf("malformed identity output was not separated: %s", output)
	}
}

func TestIdentityCheckModelIsInputError(t *testing.T) {
	if _, _, _, _, _, _, err := parseIdentity([]string{"--check-model", "gpt-test"}); err == nil {
		t.Fatal("identity accepted --check-model")
	}
}
