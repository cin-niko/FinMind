import { strict as assert } from "node:assert";
import { renderToStaticMarkup } from "react-dom/server";
import { AppShell } from "./AppShell";
import { createNewConversation } from "../chat/mockChat";

const markup = renderToStaticMarkup(
  <AppShell
    active="chat"
    role="admin"
    conversations={[createNewConversation("Review request")]}
    selectedChatId="missing"
    onLogout={() => undefined}
    onNavigate={() => undefined}
    onRenameConversation={() => undefined}
    onDeleteConversation={() => undefined}
    onSelectChat={() => undefined}
  >
    <div>Content</div>
  </AppShell>
);

assert.match(markup, /aria-label="Conversation actions"/);
assert.match(markup, /aria-haspopup="menu"/);
assert.doesNotMatch(markup, /Remove from project/);
assert.doesNotMatch(markup, /aria-label="Rename conversation"/);
assert.doesNotMatch(markup, /aria-label="Delete conversation"/);
