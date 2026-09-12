export interface RubricLevel {
    level: string;
    text: string;
}

/**
 * Rubric được nhập dưới các dạng phổ biến:
 * - "1: ... 2: ... 3: ..."
 * - "1. ... 2. ... 3. ..."
 * - "Mức 1: ... Mức 2: ... Mức 3: ..."
 * - "Level 1: ... Level 2: ... Level 3: ..."
 * 
 * Tách thành từng mức có cấu trúc để hiển thị bảng rõ ràng, tối ưu trải nghiệm
 * cho Interviewer trong lúc phỏng vấn. Nếu không có định dạng phân mức, fallback
 * về hiển thị nguyên văn.
 */
export function parseRubric(rubric: string | null | undefined): RubricLevel[] {
    if (!rubric || !rubric.trim()) {
        return [];
    }

    const trimmed = rubric.trim();
    // Bắt các pattern: "1:", "1.", "Mức 1:", "Level 1:" (không phân biệt hoa thường)
    const regex = /(?:(?:mức|level)\s+)?(\d+)[:.]\s*/gi;
    const matches = [...trimmed.matchAll(regex)];

    if (matches.length === 0) {
        return [{ level: "", text: trimmed }];
    }

    return matches.map((m, i) => {
        const start = m.index! + m[0].length;
        const end = i + 1 < matches.length ? matches[i + 1].index! : trimmed.length;
        return {
            level: m[1],
            text: trimmed.slice(start, end).trim(),
        };
    });
}