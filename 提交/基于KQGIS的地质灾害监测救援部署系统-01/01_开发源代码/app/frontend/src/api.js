function csrfToken() {
  return (
    document.cookie
      .split("; ")
      .find((item) => item.startsWith("csrftoken="))
      ?.split("=")[1] || ""
  );
}

export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...(options.method && options.method !== "GET"
        ? { "X-CSRFToken": csrfToken() }
        : {}),
      ...options.headers,
    },
  });
  let result = {};
  try {
    result = await response.json();
  } catch {
    /* service may be offline */
  }
  if (!response.ok)
    throw new Error(result.error || `请求失败 (${response.status})`);
  return result;
}

export const post = (path, value) =>
  api(path, { method: "POST", body: JSON.stringify(value) });
export const patch = (path, value) =>
  api(path, { method: "PATCH", body: JSON.stringify(value) });
export const remove = (path) => api(path, { method: "DELETE" });
