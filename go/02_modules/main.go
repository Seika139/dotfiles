package main

import (
	"fmt"
	"log"

	"github.com/google/uuid"
)

func main() {
	// 1. 新しいUUID（Version 4）を生成
	newID := uuid.New()
	fmt.Printf("生成されたUUID: %s\n", newID.String())

	// 2. UUIDのバージョンを確認（通常は 4）
	fmt.Printf("UUID バージョン: %d\n", newID.Version())

	// 3. 文字列からUUIDをパースする例
	idStr := "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
	parsedID, err := uuid.Parse(idStr)
	if err != nil {
		log.Fatalf("パース失敗: %v", err)
	}

	fmt.Printf("パース成功: %s (Variant: %d)\n", parsedID, parsedID.Variant())
}
