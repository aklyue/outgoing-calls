import { useState } from "react";
import { extractAndNormalizeFirstPhone } from "../../utils/tools";
import * as XLSX from "xlsx";

interface UseCallFileManagerResult {
  normalizeCallList: (file: File) => Promise<Blob>;
}

export const useCallFileManager = ({
  normalizeCallList,
}: UseCallFileManagerResult) => {
  const [columns, setColumns] = useState<string[]>([]);
  const [finalDf, setFinalDf] = useState<any[]>([]);
  const [fileName, setFileName] = useState("");

  const [phoneColumn, setPhoneColumn] = useState("");

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);

    try {
      const normalizedBlob = await normalizeCallList(file);
      const data = new Uint8Array(await normalizedBlob.arrayBuffer());

      const wb = XLSX.read(data, { type: "array" });
      const wsName = wb.SheetNames[0];
      const ws = wb.Sheets[wsName];

      const rows = XLSX.utils.sheet_to_json(ws, { defval: "" }) as any[];

      if (rows.length > 0) {
        const cols = Object.keys(rows[0]);
        setColumns(cols);

        const autoPhone =
          cols.find((c) => /телефон|phone|tel/i.test(c)) || cols[0] || "";
        setPhoneColumn(autoPhone);

        const processed = rows.map((row) => ({
          ...row,
          [autoPhone]:
            extractAndNormalizeFirstPhone(String(row[autoPhone] || "")) || "",
        }));

        setFinalDf(processed);
        console.log("Загружено строк:", processed.length);
      }
    } catch (error) {
      console.error("Ошибка при загрузке файла:", error);
    }
  };

  return {
    columns,
    finalDf,
    phoneColumn,
    setPhoneColumn,
    handleFileUpload,
    fileName,
  };
};
