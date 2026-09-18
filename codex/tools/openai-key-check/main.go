package main

import (
	"bufio"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"math"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"golang.org/x/term"
)

const (
	baseURL        = "https://api.openai.com/v1/models"
	identityURL    = "https://api.openai.com/v1/me"
	maxBody        = 1 << 20
	cleanEnvMarker = "OPENAI_KEY_CHECK_CLEAN_ENV"
)

type result struct {
	SchemaVersion  int            `json:"schema_version"`
	Status         string         `json:"status"`
	ModelsEndpoint modelsEndpoint `json:"models_endpoint"`
	ModelEndpoint  *endpoint      `json:"model_endpoint,omitempty"`
}
type endpoint struct {
	Outcome   string            `json:"outcome"`
	Status    int               `json:"status,omitempty"`
	Headers   map[string]string `json:"headers,omitempty"`
	ErrorType string            `json:"error_type,omitempty"`
	ErrorCode string            `json:"error_code,omitempty"`
}
type modelsEndpoint struct {
	Outcome             string            `json:"outcome"`
	Status              int               `json:"status,omitempty"`
	Headers             map[string]string `json:"headers,omitempty"`
	ErrorType           string            `json:"error_type,omitempty"`
	ErrorCode           string            `json:"error_code,omitempty"`
	Models              *[]model          `json:"models,omitempty"`
	ModelCount          *int              `json:"model_count,omitempty"`
	ModelsTruncated     *bool             `json:"models_truncated,omitempty"`
	MetadataUnavailable bool              `json:"metadata_unavailable,omitempty"`
}

type identityResult struct {
	Schema                      string         `json:"schema"`
	SchemaVersion               int            `json:"schema_version"`
	Status                      string         `json:"status"`
	IdentityEndpoint            endpoint       `json:"identity_endpoint"`
	Identity                    map[string]any `json:"identity,omitempty"`
	IdentityMetadataUnavailable bool           `json:"identity_metadata_unavailable,omitempty"`
}

func applyVerbosity(out *result, verbose bool) {
	if verbose {
		return
	}
	out.ModelsEndpoint.Headers = nil
	out.ModelsEndpoint.Models = nil
	out.ModelsEndpoint.ModelsTruncated = nil
	if out.ModelEndpoint != nil {
		out.ModelEndpoint.Headers = nil
	}
}

type model struct {
	ID           string `json:"id"`
	OwnedBy      string `json:"owned_by,omitempty"`
	Created      any    `json:"created,omitempty"`
	ShutdownDate any    `json:"shutdown_date,omitempty"`
}

func safeHeaders(h http.Header) map[string]string {
	out := map[string]string{}
	allowed := map[string]struct{}{
		"x-request-id":                         {},
		"openai-organization":                  {},
		"openai-project":                       {},
		"openai-processing-ms":                 {},
		"openai-version":                       {},
		"x-ratelimit-limit-requests":           {},
		"x-ratelimit-limit-tokens":             {},
		"x-ratelimit-remaining-requests":       {},
		"x-ratelimit-remaining-tokens":         {},
		"x-ratelimit-reset-requests":           {},
		"x-ratelimit-reset-tokens":             {},
		"x-ratelimit-limit-project-tokens":     {},
		"x-ratelimit-remaining-project-tokens": {},
		"x-ratelimit-reset-project-tokens":     {},
	}
	for k, values := range h {
		lk := strings.ToLower(k)
		if _, ok := allowed[lk]; ok {
			if len(values) > 0 {
				out[lk] = values[0]
			}
		}
	}
	return out
}
func readBody(r io.ReadCloser) ([]byte, bool, bool) {
	defer r.Close()
	b, err := io.ReadAll(io.LimitReader(r, maxBody+1))
	tooLarge := len(b) > maxBody
	if tooLarge {
		b = b[:maxBody]
	}
	return b, tooLarge, err != nil
}
func errorFields(body []byte) (string, string) {
	var v struct {
		Error struct {
			Type any `json:"type"`
			Code any `json:"code"`
		} `json:"error"`
	}
	if json.Unmarshal(body, &v) != nil {
		return "", ""
	}
	t, _ := v.Error.Type.(string)
	c, _ := v.Error.Code.(string)
	return t, c
}
func codeFor(status int) int {
	switch status {
	case 401:
		return 10
	case 403:
		return 11
	case 429:
		return 12
	default:
		return 13
	}
}

func request(client *http.Client, key, organization, project, target string) (endpoint, int, []byte, bool, bool) {
	req, err := http.NewRequest(http.MethodGet, target, nil)
	if err != nil {
		return endpoint{Outcome: "indeterminate"}, 14, nil, false, false
	}
	req.Header.Set("Authorization", "Bearer "+key)
	if organization != "" {
		req.Header.Set("OpenAI-Organization", organization)
	}
	if project != "" {
		req.Header.Set("OpenAI-Project", project)
	}
	resp, err := client.Do(req)
	if err != nil {
		return endpoint{Outcome: "indeterminate", ErrorType: "network"}, 14, nil, false, false
	}
	body, tooLarge, readErr := readBody(resp.Body)
	e := endpoint{Status: resp.StatusCode, Headers: safeHeaders(resp.Header)}
	if resp.StatusCode != http.StatusOK {
		e.Outcome = "rejected"
		e.ErrorType, e.ErrorCode = errorFields(body)
		return e, codeFor(resp.StatusCode), nil, false, false
	}
	e.Outcome = "endpoint_accessible"
	if readErr {
		return e, 0, nil, false, true
	}
	return e, 0, body, tooLarge, readErr
}
func setEmptyMetadata(e *modelsEndpoint) {
	e.Models = nil
	e.ModelCount = nil
	e.ModelsTruncated = nil
}
func markMetadataUnavailable(e *modelsEndpoint) {
	setEmptyMetadata(e)
	e.MetadataUnavailable = true
}
func summarize(e *modelsEndpoint, body []byte) {
	setEmptyMetadata(e)
	e.MetadataUnavailable = false
	var v struct {
		Data json.RawMessage `json:"data"`
	}
	if json.Unmarshal(body, &v) != nil {
		e.MetadataUnavailable = true
		return
	}
	dataJSON := strings.TrimSpace(string(v.Data))
	if len(v.Data) == 0 || dataJSON == "null" || len(dataJSON) == 0 || dataJSON[0] != '[' {
		e.MetadataUnavailable = true
		return
	}
	var data []map[string]any
	if json.Unmarshal(v.Data, &data) != nil {
		e.MetadataUnavailable = true
		return
	}
	for _, x := range data {
		id, ok := x["id"].(string)
		if !ok || id == "" {
			markMetadataUnavailable(e)
			return
		}
	}
	models := make([]model, 0, min(len(data), 100))
	count := 0
	truncated := false
	for _, x := range data {
		id := x["id"].(string)
		count++
		if len(models) >= 100 {
			truncated = true
			continue
		}
		m := model{ID: id}
		if s, ok := x["owned_by"].(string); ok {
			m.OwnedBy = s
		}
		if v, ok := metadataValue(x["created"]); ok {
			m.Created = v
		}
		if v, ok := metadataValue(x["shutdown_date"]); ok {
			m.ShutdownDate = v
		}
		models = append(models, m)
	}
	e.Models = &models
	e.ModelCount = &count
	e.ModelsTruncated = &truncated
}

func modelsResult(e endpoint, body []byte, tooLarge, bodyReadErr bool) modelsEndpoint {
	out := modelsEndpoint{Outcome: e.Outcome, Status: e.Status, Headers: e.Headers, ErrorType: e.ErrorType, ErrorCode: e.ErrorCode}
	if bodyReadErr || tooLarge {
		markMetadataUnavailable(&out)
	} else if body != nil {
		summarize(&out, body)
	}
	return out
}

func identityMetadata(e endpoint, body []byte, tooLarge, bodyReadErr, verbose bool) (map[string]any, bool) {
	if bodyReadErr || tooLarge || body == nil {
		return nil, true
	}
	var raw map[string]any
	if err := json.Unmarshal(body, &raw); err != nil || raw == nil {
		return nil, true
	}
	userID, idOK := rawString(raw, "id")
	created, createdOK := rawUnix(raw, "created")
	name, nameOK := rawString(raw, "name")
	if !idOK || !createdOK || !nameOK {
		return nil, true
	}
	orgs, orgsOK := rawObject(raw, "orgs")
	if !orgsOK {
		return nil, true
	}
	data, dataOK := rawArray(orgs, "data")
	if !dataOK {
		return nil, true
	}
	validatedOrgs := make([]map[string]any, 0, len(data))
	for _, item := range data {
		org, ok := item.(map[string]any)
		if !ok {
			return nil, true
		}
		out, valid := identityOrganization(org, verbose)
		if !valid {
			return nil, true
		}
		validatedOrgs = append(validatedOrgs, out)
	}
	identity := map[string]any{
		"id":      userID,
		"created": time.Unix(created, 0).UTC().Format(time.RFC3339),
		"name":    name,
		"orgs":    validatedOrgs,
	}
	if verbose {
		copyIdentityVerboseFields(identity, raw)
		identity["created_unix"] = created
	}
	return identity, false
}

func identityOrganization(raw map[string]any, verbose bool) (map[string]any, bool) {
	id, idOK := rawString(raw, "id")
	if !idOK {
		return nil, false
	}
	out := map[string]any{"id": id}
	name, nameOK := rawString(raw, "name")
	title, titleOK := rawString(raw, "title")
	if !nameOK || !titleOK {
		return nil, false
	}
	out["name"] = name
	out["title"] = title
	if created, ok := rawUnix(raw, "created"); ok {
		out["created"] = time.Unix(created, 0).UTC().Format(time.RFC3339)
		if verbose {
			out["created_unix"] = created
		}
	}
	if verbose {
		copyOrganizationVerboseFields(out, raw)
	}
	return out, true
}

func copyScalarFields(dst, src map[string]any, fields []string) {
	for _, field := range fields {
		value, ok := src[field]
		if !ok || value == nil {
			continue
		}
		switch value.(type) {
		case string, bool, float64:
			dst[field] = value
		}
	}
}

func copyIdentityVerboseFields(dst, src map[string]any) {
	copyScalarFields(dst, src, []string{"object", "email", "email_domain_type", "ads_segment_id", "has_payg_project_spend_limit", "mfa_flag_enabled", "phone_number", "picture"})
	if amr, ok := src["amr"].([]any); ok {
		values := make([]string, 0, len(amr))
		for _, value := range amr {
			item, ok := value.(string)
			if !ok {
				values = nil
				break
			}
			values = append(values, item)
		}
		if values != nil {
			dst["amr"] = values
		}
	}
}

func copyOrganizationVerboseFields(dst, src map[string]any) {
	copyScalarFields(dst, src, []string{"object", "description", "is_default", "is_scale_tier_authorized_purchaser", "is_scim_managed", "parent_org_id", "personal", "role"})
	if settings, ok := src["settings"].(map[string]any); ok {
		filtered := map[string]any{}
		copyScalarFields(filtered, settings, []string{"completed_platform_onboarding", "disable_user_api_keys", "threads_ui_visibility", "usage_dashboard_visibility"})
		if len(filtered) > 0 {
			dst["settings"] = filtered
		}
	}
}

func rawString(raw map[string]any, field string) (string, bool) {
	v, ok := raw[field].(string)
	return v, ok && v != ""
}

func rawUnix(raw map[string]any, field string) (int64, bool) {
	v, ok := raw[field].(float64)
	if !ok || math.IsNaN(v) || math.IsInf(v, 0) || v != math.Trunc(v) || v < -9223372036854775808.0 || v >= 9223372036854775808.0 {
		return 0, false
	}
	return int64(v), true
}

func rawObject(raw map[string]any, field string) (map[string]any, bool) {
	v, ok := raw[field].(map[string]any)
	return v, ok && v != nil
}

func rawArray(raw map[string]any, field string) ([]any, bool) {
	v, ok := raw[field].([]any)
	return v, ok
}

func metadataValue(v any) (any, bool) {
	switch v.(type) {
	case string, float64, bool:
		return v, true
	default:
		return nil, false
	}
}
func validValue(s string) bool { return s != "" && !strings.ContainsAny(s, "\r\n\x00") }
func readKey(stdin bool) (string, error) {
	if stdin {
		if term.IsTerminal(int(os.Stdin.Fd())) {
			return "", errors.New("stdin is a tty")
		}
		return readStdinKey(os.Stdin)
	}
	if !term.IsTerminal(int(os.Stdin.Fd())) {
		return "", errors.New("secure terminal unavailable")
	}
	fmt.Fprint(os.Stderr, "OpenAI API key: ")
	b, err := term.ReadPassword(int(os.Stdin.Fd()))
	fmt.Fprintln(os.Stderr)
	if err != nil || len(b) == 0 || len(b) > 4096 || bytesHasCtl(b) {
		return "", errors.New("invalid key")
	}
	return string(b), nil
}
func readStdinKey(input io.Reader) (string, error) {
	r := bufio.NewReader(io.LimitReader(input, 4097))
	b, err := r.ReadBytes('\n')
	if err != nil && len(b) == 0 {
		return "", errors.New("empty key")
	}
	b = bytesTrimLine(b)
	if len(b) > 4096 {
		return "", errors.New("key too long")
	}
	if len(b) == 0 || bytesHasCtl(b) {
		return "", errors.New("invalid key")
	}
	return string(b), nil
}
func bytesTrimLine(b []byte) []byte {
	if len(b) > 0 && b[len(b)-1] == '\n' {
		b = b[:len(b)-1]
	}
	if len(b) > 0 && b[len(b)-1] == '\r' {
		b = b[:len(b)-1]
	}
	return b
}
func bytesHasCtl(b []byte) bool { return strings.ContainsAny(string(b), "\r\n\x00") }
func parse(args []string) (string, string, string, string, float64, bool, bool, error) {
	var org, proj, modelID string
	var timeout float64
	var stdin, verbose bool
	fs := flag.NewFlagSet("openai-key-check", flag.ContinueOnError)
	fs.SetOutput(io.Discard)
	fs.StringVar(&org, "organization", "", "")
	fs.StringVar(&proj, "project", "", "")
	fs.StringVar(&modelID, "check-model", "", "")
	fs.Float64Var(&timeout, "timeout", 15, "")
	fs.BoolVar(&stdin, "api-key-stdin", false, "")
	fs.BoolVar(&verbose, "verbose", false, "")
	if err := fs.Parse(args); err != nil {
		return "", "", "", "", 0, false, false, errors.New("invalid input")
	}
	if fs.NArg() != 0 || !validValueOptional(org) || !validValueOptional(proj) || !validValueOptional(modelID) || !validTimeout(timeout) {
		return "", "", "", "", 0, false, false, errors.New("invalid input")
	}
	key, err := readKey(stdin)
	return key, org, proj, modelID, timeout, stdin, verbose, err
}

func parseIdentity(args []string) (string, string, string, float64, bool, bool, error) {
	var org, proj, modelID string
	var timeout float64
	var stdin, verbose bool
	fs := flag.NewFlagSet("openai-key-check identity", flag.ContinueOnError)
	fs.SetOutput(io.Discard)
	fs.StringVar(&org, "organization", "", "")
	fs.StringVar(&proj, "project", "", "")
	fs.StringVar(&modelID, "check-model", "", "")
	fs.Float64Var(&timeout, "timeout", 15, "")
	fs.BoolVar(&stdin, "api-key-stdin", false, "")
	fs.BoolVar(&verbose, "verbose", false, "")
	if err := fs.Parse(args); err != nil || fs.NArg() != 0 || modelID != "" || !validValueOptional(org) || !validValueOptional(proj) || !validTimeout(timeout) {
		return "", "", "", 0, false, false, errors.New("invalid input")
	}
	key, err := readKey(stdin)
	return key, org, proj, timeout, stdin, verbose, err
}
func validTimeout(seconds float64) bool {
	if seconds <= 0 || math.IsNaN(seconds) || math.IsInf(seconds, 0) {
		return false
	}
	maxSeconds := float64(time.Duration(1<<63-1)) / float64(time.Second)
	if seconds > maxSeconds {
		return false
	}
	d := time.Duration(seconds * float64(time.Second))
	return d > 0 && d <= time.Duration(1<<63-1)
}
func timeoutDuration(seconds float64) (time.Duration, bool) {
	if !validTimeout(seconds) {
		return 0, false
	}
	return time.Duration(seconds * float64(time.Second)), true
}
func validValueOptional(s string) bool { return s == "" || validValue(s) }

var httpClientFactory = func(requestTimeout time.Duration) *http.Client {
	tr := http.DefaultTransport.(*http.Transport).Clone()
	tr.Proxy = nil
	return &http.Client{Transport: tr, Timeout: requestTimeout, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
}

func runModels(args []string) int {
	key, org, proj, modelID, timeout, _, verbose, err := parse(args)
	if err != nil {
		printJSON(map[string]any{"schema_version": 3, "status": "input_error", "error": "invalid input"})
		return 2
	}
	requestTimeout, _ := timeoutDuration(timeout)
	client := httpClientFactory(requestTimeout)
	out := result{SchemaVersion: 3, Status: "indeterminate"}
	e, c, b, tooLarge, bodyReadErr := request(client, key, org, proj, baseURL)
	out.ModelsEndpoint = modelsResult(e, b, tooLarge, bodyReadErr)
	final := c
	if modelID != "" {
		u := baseURL + "/" + url.PathEscape(modelID)
		me, mc, _, _, _ := request(client, key, org, proj, u)
		out.ModelEndpoint = &me
		if mc != 0 {
			final = mc
		}
	}
	if final == 0 {
		out.Status = "endpoint_accessible"
	} else if final <= 13 {
		out.Status = "rejected"
	}
	applyVerbosity(&out, verbose)
	printJSON(out)
	return final
}

func runIdentity(args []string) int {
	key, org, proj, timeout, _, verbose, err := parseIdentity(args)
	if err != nil {
		printJSON(identityResult{Schema: "openai-key-check/identity", SchemaVersion: 1, Status: "input_error"})
		return 2
	}
	requestTimeout, _ := timeoutDuration(timeout)
	client := httpClientFactory(requestTimeout)
	e, code, body, tooLarge, bodyReadErr := request(client, key, org, proj, identityURL)
	out := identityResult{
		Schema:           "openai-key-check/identity",
		SchemaVersion:    1,
		Status:           "indeterminate",
		IdentityEndpoint: e,
	}
	if code == 0 {
		out.Status = "endpoint_accessible"
		out.Identity, out.IdentityMetadataUnavailable = identityMetadata(e, body, tooLarge, bodyReadErr, verbose)
	} else if code <= 13 {
		out.Status = "rejected"
	}
	if !verbose {
		out.IdentityEndpoint.Headers = nil
	}
	printJSON(out)
	return code
}

func run(args []string) int {
	if len(args) > 0 {
		switch args[0] {
		case "identity":
			return runIdentity(args[1:])
		case "models":
			return runModels(args[1:])
		}
	}
	return runModels(args)
}
func printJSON(v any) { b, _ := json.Marshal(v); fmt.Fprintln(os.Stdout, string(b)) }

func cleanEnvironment(env []string) bool {
	return len(env) == 1 && env[0] == cleanEnvMarker+"=1"
}

func main() {
	if !cleanEnvironment(os.Environ()) {
		exe, err := os.Executable()
		if err != nil {
			printJSON(map[string]any{"schema_version": 3, "status": "indeterminate", "error": "process startup failed"})
			os.Exit(14)
		}
		proc, err := os.StartProcess(exe, append([]string{exe}, os.Args[1:]...), &os.ProcAttr{
			Env:   []string{cleanEnvMarker + "=1"},
			Files: []*os.File{os.Stdin, os.Stdout, os.Stderr},
		})
		if err != nil {
			printJSON(map[string]any{"schema_version": 3, "status": "indeterminate", "error": "process startup failed"})
			os.Exit(14)
		}
		state, err := proc.Wait()
		if err != nil {
			printJSON(map[string]any{"schema_version": 3, "status": "indeterminate", "error": "process startup failed"})
			os.Exit(14)
		}
		os.Exit(state.ExitCode())
	}
	os.Clearenv()
	os.Exit(run(os.Args[1:]))
}
