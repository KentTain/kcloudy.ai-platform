export const notifySuccess = (message: string) => {
  console.info(message);
};

export const notifyError = (message: string) => {
  console.error(message);
};

export const confirmAction = (message: string) => window.confirm(message);

export const getErrorMessage = (error: unknown, fallback: string) => {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { msg?: string; detail?: string } } }).response;
    return response?.data?.msg || response?.data?.detail || fallback;
  }

  if (error instanceof Error) {
    return error.message || fallback;
  }

  return fallback;
};
