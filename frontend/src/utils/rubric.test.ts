import test from "node:test";
import assert from "node:assert/strict";
import { parseRubric } from "./rubric.ts";

test("Eval 1: Parse standard rubric format (1: ... 2: ...)", () => {
    const raw = "1: Kém 2: Đạt 3: Tốt";
    const result = parseRubric(raw);
    assert.equal(result.length, 3);
    assert.equal(result[0].level, "1");
    assert.equal(result[0].text, "Kém");
    assert.equal(result[1].level, "2");
    assert.equal(result[1].text, "Đạt");
    assert.equal(result[2].level, "3");
    assert.equal(result[2].text, "Tốt");
});

test("Eval 2: Parse dot notation format (1. ... 2. ...)", () => {
    const raw = "1. Chưa đạt\n2. Đạt chuẩn\n3. Xuất sắc";
    const result = parseRubric(raw);
    assert.equal(result.length, 3);
    assert.equal(result[0].level, "1");
    assert.equal(result[0].text, "Chưa đạt");
    assert.equal(result[1].level, "2");
    assert.equal(result[1].text, "Đạt chuẩn");
    assert.equal(result[2].level, "3");
    assert.equal(result[2].text, "Xuất sắc");
});

test("Eval 3: Parse Vietnamese 'Mức N:' or 'Level N:' prefix", () => {
    const raw = "Mức 1: Không đạt yêu cầu. Mức 2: Tạm ổn. Mức 3: Làm chủ công nghệ.";
    const result = parseRubric(raw);
    assert.equal(result.length, 3);
    assert.equal(result[0].level, "1");
    assert.equal(result[0].text, "Không đạt yêu cầu.");
    assert.equal(result[1].level, "2");
    assert.equal(result[1].text, "Tạm ổn.");
    assert.equal(result[2].level, "3");
    assert.equal(result[2].text, "Làm chủ công nghệ.");
});

test("Eval 4: Graceful handling of non-formatted text", () => {
    const raw = "Chấm điểm dựa trên kinh nghiệm thực chiến và khả năng giải quyết bài toán.";
    const result = parseRubric(raw);
    assert.equal(result.length, 1);
    assert.equal(result[0].level, "");
    assert.equal(result[0].text, raw);
});

test("Eval 5: Safe handling of empty or nullish strings", () => {
    assert.deepEqual(parseRubric(""), []);
    assert.deepEqual(parseRubric("   "), []);
    // @ts-expect-error test runtime boundary
    assert.deepEqual(parseRubric(null), []);
    // @ts-expect-error test runtime boundary
    assert.deepEqual(parseRubric(undefined), []);
});
