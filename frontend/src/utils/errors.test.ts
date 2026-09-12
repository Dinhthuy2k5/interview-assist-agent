import test from "node:test";
import assert from "node:assert/strict";
import { ApiError, parseApiErrorMessage } from "./errors.ts";

test("Eval 1: Parse simple FastAPI detail string", () => {
    const jsonBody = JSON.stringify({ detail: "Tên vị trí đã tồn tại." });
    const message = parseApiErrorMessage(jsonBody, 400);
    assert.equal(message, "Tên vị trí đã tồn tại.");
});

test("Eval 2: Parse FastAPI 422 validation error array", () => {
    const jsonBody = JSON.stringify({
        detail: [
            {
                loc: ["body", "email"],
                msg: "value is not a valid email address",
                type: "value_error",
            },
        ],
    });
    const message = parseApiErrorMessage(jsonBody, 422);
    assert.equal(message, "email: value is not a valid email address");
});

test("Eval 3: Parse multiple validation errors into readable list", () => {
    const jsonBody = JSON.stringify({
        detail: [
            { loc: ["body", "username"], msg: "Field required" },
            { loc: ["body", "password"], msg: "Too short" },
        ],
    });
    const message = parseApiErrorMessage(jsonBody, 422);
    assert.equal(message, "username: Field required; password: Too short");
});

test("Eval 4: Fallback gracefully when response is HTML or plain text", () => {
    const htmlBody = "<html><body>502 Bad Gateway</body></html>";
    const message = parseApiErrorMessage(htmlBody, 502);
    assert.match(message, /502|Bad Gateway|Máy chủ/);
});

test("Eval 5: Fallback based on HTTP status code when body is empty", () => {
    assert.equal(parseApiErrorMessage("", 404), "Không tìm thấy dữ liệu yêu cầu.");
    assert.equal(parseApiErrorMessage("", 403), "Bạn không có quyền thực hiện hành động này.");
    assert.equal(parseApiErrorMessage("", 500), "Lỗi máy chủ nội bộ. Vui lòng thử lại sau.");
});

test("Eval 6: ApiError class properties and inheritance", () => {
    const err = new ApiError(400, "Dữ liệu không hợp lệ", '{"detail":"Dữ liệu không hợp lệ"}');
    assert.equal(err instanceof Error, true);
    assert.equal(err.name, "ApiError");
    assert.equal(err.status, 400);
    assert.equal(err.message, "Dữ liệu không hợp lệ");
    assert.equal(err.rawBody, '{"detail":"Dữ liệu không hợp lệ"}');
});
