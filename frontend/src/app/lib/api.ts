import type {
  OptimizeQueryResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;

  constructor(
    message: string,
    status: number,
  ) {
    super(message);

    this.name = "ApiError";
    this.status = status;
  }
}

async function readErrorMessage(
  response: Response,
): Promise<string> {
  try {
    const data = await response.json();

    if (
      data &&
      typeof data.detail === "string"
    ) {
      return data.detail;
    }

    if (
      data &&
      Array.isArray(data.detail)
    ) {
      return data.detail
        .map(
          (
            item: {
              msg?: string;
            },
          ) => item.msg,
        )
        .filter(Boolean)
        .join(", ");
    }
  } catch {
    // Response JSON değilse varsayılan mesaj kullanılır.
  }

  return `Request failed with status ${response.status}`;
}

export async function optimizeQuery(
  databaseId: number,
  query: string,
): Promise<OptimizeQueryResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/databases/${databaseId}/optimize-query`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        query,
      }),
    },
  );

  if (!response.ok) {
    const message =
      await readErrorMessage(response);

    throw new ApiError(
      message,
      response.status,
    );
  }

  return response.json();
}