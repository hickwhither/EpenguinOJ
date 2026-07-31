import { toast } from "react-toastify";
const BASE_URL = "/api";

export async function request(path, options = {}) {
  const config = {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    credentials: "include",
    body: options.body ? JSON.stringify(options.body) : undefined
  };

  try {
    const res = await fetch(BASE_URL + path, config);

    // Rate limit
    if (res.status === 429) {
      toast.error("429. Slow down, buddy");
      return { data: null, status: 429 };
    }

    const data = await res.json();
    return {
      data: data,
      status: res.status
    };

  } catch (error) {
    console.error("API Error:", String(error));
    toast.error("A system error occurred or the network connection was lost!");
    return {
      data: {detail: error},
      status: error.status || 500 
    };
  }
}

export async function get_request(path, extra = {}) {
  return request(path, {
    method: "GET",
    ...extra
  });
}

export async function post_request(path, body = {}, extra = {}) {
  return request(path, {
    method: "POST",
    body: body,
    ...extra
  });
}