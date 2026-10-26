import { toast } from "sonner";

/**
 * 上传文件在消息内容中的块格式。
 *
 * 采用 LangChain v0 标准数据块（source_type + snake_case mime_type），
 * Python 侧 langchain_core 才能识别并转换为 OpenAI 的 image_url / file_data；
 * 若用 @langchain/core 的 v1 格式（mimeType + data），Python 会原样透传导致 400。
 */
export type Base64FileBlock = {
  type: "image" | "file";
  source_type: "base64";
  data: string;
  mime_type: string;
  metadata?: { name?: string; filename?: string };
};

export const SUPPORTED_IMAGE_TYPES = [
  "image/jpeg",
  "image/png",
  "image/gif",
  "image/webp",
];

export const SUPPORTED_FILE_TYPES = [
  ...SUPPORTED_IMAGE_TYPES,
  "application/pdf",
];

// Returns a Promise of a typed multimodal block for images or PDFs
export async function fileToContentBlock(
  file: File,
): Promise<Base64FileBlock> {
  if (!SUPPORTED_FILE_TYPES.includes(file.type)) {
    toast.error(
      `不支持的文件类型：${file.type}。支持的类型：${SUPPORTED_FILE_TYPES.join(", ")}`,
    );
    return Promise.reject(new Error(`Unsupported file type: ${file.type}`));
  }

  const data = await fileToBase64(file);

  if (SUPPORTED_IMAGE_TYPES.includes(file.type)) {
    return {
      type: "image",
      source_type: "base64",
      data,
      mime_type: file.type,
      metadata: { name: file.name },
    };
  }

  // PDF
  return {
    type: "file",
    source_type: "base64",
    data,
    mime_type: "application/pdf",
    metadata: { filename: file.name },
  };
}

// Helper to convert File to base64 string
export async function fileToBase64(file: File): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result as string;
      // Remove the data:...;base64, prefix
      resolve(result.split(",")[1]);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

// Type guard for Base64ContentBlock
export function isBase64ContentBlock(
  block: unknown,
): block is Base64FileBlock {
  if (typeof block !== "object" || block === null) return false;
  const b = block as Record<string, unknown>;
  if (b.source_type !== "base64" || typeof b.data !== "string") return false;
  if (typeof b.mime_type !== "string") return false;
  if (b.type === "file") return b.mime_type === "application/pdf";
  if (b.type === "image") return b.mime_type.startsWith("image/");
  return false;
}
