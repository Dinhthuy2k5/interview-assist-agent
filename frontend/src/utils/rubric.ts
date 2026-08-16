export interface RubricLevel {
    level: string;
    text: string;
}

/** Rubric được nhập dạng "1: ... 2: ... 3: ..." - tách thành từng mức để hiển thị
 *  dạng bảng thay vì 1 đoạn văn dài khó quét mắt. Nếu không khớp pattern "N: ",
 *  fallback về hiển thị nguyên văn (level rỗng). */
export function parseRubric(rubric: string): RubricLevel[] {
    const matches = [...rubric.matchAll(/(\d+):\s*/g)];
    if (matches.length === 0) return [{ level: "", text: rubric }];

    return matches.map((m, i) => {
        const start = m.index! + m[0].length;
        const end = i + 1 < matches.length ? matches[i + 1].index! : rubric.length;
        return { level: m[1], text: rubric.slice(start, end).trim() };
    });
}