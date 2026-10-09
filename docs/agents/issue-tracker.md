# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues on `kendrick/long-term-memory-kit`.

## Writes go through GraphQL

Make every write with a `gh api graphql` mutation, and pass each body as a file (`-F body=@body.md`). The maintainer's network blocks `gh issue create|edit|comment|close` and REST writes, so a GraphQL mutation is the first and only attempt. Reads through `gh issue view`, `gh issue list`, or REST work normally.

Mutations take node ids, never `#number` or database ids. Look them up first:

- Repository id: `gh api graphql -f query='{repository(owner:"kendrick",name:"long-term-memory-kit"){id}}' --jq .data.repository.id`
- Issue id: `gh api graphql -f query='{repository(owner:"kendrick",name:"long-term-memory-kit"){issue(number:N){id}}}' --jq .data.repository.issue.id`
- Label ids: `gh api graphql -f query='{repository(owner:"kendrick",name:"long-term-memory-kit"){labels(first:50){nodes{id name}}}}'`

## Conventions

- **Create an issue**: `createIssue(input:{repositoryId, title, body, labelIds})`.
- **Read an issue**: `gh issue view <number> --json number,title,body,labels,comments`.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with `--label` and `--state` filters as needed.
- **Make an issue a sub-issue of a parent**: `addSubIssue(input:{issueId:<parent>, subIssueId:<child>})`.
- **Comment on an issue**: `addComment(input:{subjectId:<issue>, body})`.
- **Apply / remove labels**: `addLabelsToLabelable(input:{labelableId:<issue>, labelIds})` / `removeLabelsFromLabelable(...)`.
- **Close**: `addComment` with the closing note, then `closeIssue(input:{issueId, stateReason:COMPLETED})`.
- **Assign**: `addAssigneesToAssignable(input:{assignableId:<issue>, assigneeIds})`; the viewer's id comes from `{viewer{id}}`.

Example:

```sh
gh api graphql \
  -f query='mutation($r:ID!,$t:String!,$b:String!){createIssue(input:{repositoryId:$r,title:$t,body:$b}){issue{number url}}}' \
  -f r="$REPO_ID" -f t="Spike: Bun-compiled MCP binary" -F b=@body.md
```

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same labels and states as issues. Read them with `gh pr view <number> --comments` and `gh pr diff <number>`, and write to them with the same mutations as issues (a PR's node id works as `subjectId`, `labelableId`, and `assignableId`).

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh pr view 42` and fall back to `gh issue view 42`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue with `createIssue`.

## When a skill says "fetch the relevant ticket"

Read it as in **Read an issue** above.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. Create it with `createIssue` and that label's id.
- **Child ticket**: an issue linked to the map with `addSubIssue`. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: GitHub's native issue dependencies. Add an edge with `addBlockedBy(input:{issueId:<child>, blockingIssueId:<blocker>})`. A ticket is unblocked when every blocker is closed; read open blockers with `gh api repos/kendrick/long-term-memory-kit/issues/<n> --jq .issue_dependencies_summary.blocked_by`.
- **Frontier query**: list the map's open sub-issues, drop any with an open blocker or an assignee; first in map order wins.
- **Claim**: `addAssigneesToAssignable` with your viewer id, the session's first write.
- **Resolve**: `addComment` with the answer, then `closeIssue`, then append a context pointer (gist + link) to the map's Decisions-so-far.
