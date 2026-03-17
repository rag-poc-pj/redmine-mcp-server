/**
 * Redmine REST API クライアント
 * Redmine API: https://www.redmine.org/projects/redmine/wiki/Rest_api
 */

export interface RedmineConfig {
  baseUrl: string;
  apiKey: string;
}

export interface Issue {
  id: number;
  project: { id: number; name: string };
  tracker: { id: number; name: string };
  status: { id: number; name: string };
  priority: { id: number; name: string };
  author: { id: number; name: string };
  assigned_to?: { id: number; name: string };
  subject: string;
  description?: string;
  start_date?: string;
  due_date?: string;
  done_ratio: number;
  created_on: string;
  updated_on: string;
}

export interface Project {
  id: number;
  name: string;
  identifier: string;
  description?: string;
  status: number;
  created_on: string;
  updated_on: string;
}

export interface IssueJournal {
  id: number;
  user: { id: number; name: string };
  notes: string;
  created_on: string;
}

export interface Attachment {
  id: number;
  filename: string;
  filesize: number;
  content_type: string;
  description?: string;
  content_url: string;
  author: { id: number; name: string };
  created_on: string;
}

export class RedmineClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(config: RedmineConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.apiKey = config.apiKey;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        "X-Redmine-API-Key": this.apiKey,
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Redmine API Error [${response.status}]: ${errorText}`);
    }

    return response.json() as Promise<T>;
  }

  // ─── Issues ──────────────────────────────────────────────

  async getIssues(params: {
    project_id?: string;
    status_id?: string;
    assigned_to_id?: string;
    subject?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ issues: Issue[]; total_count: number }> {
    const query = new URLSearchParams();
    if (params.project_id) query.set("project_id", params.project_id);
    if (params.status_id) query.set("status_id", params.status_id);
    if (params.assigned_to_id) query.set("assigned_to_id", params.assigned_to_id);
    if (params.subject) query.set("subject", `~${params.subject}`);
    query.set("limit", String(params.limit ?? 25));
    query.set("offset", String(params.offset ?? 0));

    return this.request<{ issues: Issue[]; total_count: number }>(
      `/issues.json?${query.toString()}`
    );
  }

  async getIssue(id: number): Promise<{ issue: Issue & { journals: IssueJournal[]; attachments: Attachment[] } }> {
    return this.request(`/issues/${id}.json?include=journals,attachments`);
  }

  async createIssue(data: {
    project_id: string;
    subject: string;
    description?: string;
    tracker_id?: number;
    status_id?: number;
    priority_id?: number;
    assigned_to_id?: number;
    due_date?: string;
  }): Promise<{ issue: Issue }> {
    return this.request("/issues.json", {
      method: "POST",
      body: JSON.stringify({ issue: data }),
    });
  }

  async updateIssue(
    id: number,
    data: {
      subject?: string;
      description?: string;
      status_id?: number;
      priority_id?: number;
      assigned_to_id?: number;
      due_date?: string;
      done_ratio?: number;
    }
  ): Promise<void> {
    await this.request(`/issues/${id}.json`, {
      method: "PUT",
      body: JSON.stringify({ issue: data }),
    });
  }

  async addComment(issueId: number, notes: string): Promise<void> {
    await this.request(`/issues/${issueId}.json`, {
      method: "PUT",
      body: JSON.stringify({ issue: { notes } }),
    });
  }

  // ─── Projects ─────────────────────────────────────────────

  async getProjects(params: {
    limit?: number;
    offset?: number;
  } = {}): Promise<{ projects: Project[]; total_count: number }> {
    const query = new URLSearchParams();
    query.set("limit", String(params.limit ?? 25));
    query.set("offset", String(params.offset ?? 0));
    return this.request<{ projects: Project[]; total_count: number }>(
      `/projects.json?${query.toString()}`
    );
  }

  async getProject(id: string): Promise<{ project: Project }> {
    return this.request(`/projects/${id}.json`);
  }

  // ─── Attachments ──────────────────────────────────────────

  async getAttachment(id: number): Promise<{ attachment: Attachment }> {
    return this.request(`/attachments/${id}.json`);
  }
}
