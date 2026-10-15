<a id="taxora-六项体验补齐"></a>

# Taxora: Six Experience Improvements

The user authorized the six agreed priorities while retaining a simple bilingual interface. Authentication recovery and resend entry points are implemented.

- Answers: react-markdown + remark-gfm, with raw HTML and remote images disabled and safe links opening in new tabs. Copy buttons clearly report success/failure.
- Reading: auto-follow only near the bottom; preserve position when users scroll upward and provide a return-to-bottom button. Switching conversations moves to the latest content.
- Conversations: group by update time. Rename, archive, and restore retain server-side account isolation, version checks, and idempotent requests. No permanent deletion.
- Streaming: actual model SSE passes through the backend. JSON responses display increments from the reply field only; apply facts and save only after complete structural validation. Cancellation closes the model connection without committing partial facts. If cancellation races with committing a complete response, the server's saved result is authoritative.
- Validation: isolated database tests cover account permissions, version conflicts, streaming exceptions, and cancellation. Browser tests cover layout, copying, reading position, archive/restore, and stopping. Update the local service after building.

References: official READMEs, security notes, and issues for remarkjs/react-markdown (MIT) and remarkjs/remark-gfm (MIT); DeepSeek Chat Completion SSE; Starlette StreamingResponse disconnection handling. Retain dependency licenses and do not copy external product designs.
