import { useSyncExternalStore } from 'react';

const STREAM_URL = '/api/submissions/stream';

let snapshot = {};
const listeners = new Set();
let eventSource = null;
let subscriberCount = 0;

function emit() {
  for (const listener of listeners) listener();
}

function open() {
  if (eventSource) return;
  eventSource = new EventSource(STREAM_URL);
  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.type === 'snapshot') snapshot = data.submissions || {};
    } catch {
      return;
    }
    emit();
  };
}

function close() {
  if (!eventSource) return;
  eventSource.close();
  eventSource = null;
}

export function subscribeSubmissionStream(listener) {
  listeners.add(listener);
  subscriberCount += 1;
  open();
  emit();
  return () => {
    listeners.delete(listener);
    subscriberCount -= 1;
    if (subscriberCount <= 0) {
      subscriberCount = 0;
      snapshot = {};
      close();
    }
  };
}

export function getSubmissionStreamSnapshot() {
  return snapshot;
}

export function useSubmissionStream() {
  const subs = useSyncExternalStore(
    subscribeSubmissionStream,
    getSubmissionStreamSnapshot
  );
  return { subs };
}
