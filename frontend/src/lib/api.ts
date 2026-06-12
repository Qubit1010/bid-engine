async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  const body = await res.json().catch(() => null);
  if (!res.ok || !body?.ok) {
    throw new Error(body?.detail || body?.error || `Request failed (${res.status})`);
  }
  return body.data as T;
}

export const api = {
  listWorkspaces: () => request<import("./types").Workspace[]>("/api/workspaces"),
  getWorkspace: (id: string) => request<import("./types").Workspace>(`/api/workspaces/${id}`),
  createWorkspace: (file: File, name: string) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("name", name);
    return request<import("./types").Workspace>("/api/workspaces", { method: "POST", body: fd });
  },
  runPipeline: (id: string) =>
    request<{ status: string }>(`/api/workspaces/${id}/run`, { method: "POST" }),
  deleteWorkspace: (id: string) =>
    request<{ deleted: string }>(`/api/workspaces/${id}`, { method: "DELETE" }),
  overrideRequirement: (id: string, status: string) =>
    request<import("./types").Requirement>(`/api/requirements/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }),
  updateSection: (id: string, payload: { content?: string; status?: string }) =>
    request<import("./types").DraftSection>(`/api/sections/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  regenerateSection: (id: string, feedback: string) =>
    request<import("./types").DraftSection>(`/api/sections/${id}/regenerate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ feedback }),
    }),
  validation: () => request<Record<string, unknown>>("/api/validation"),
};
