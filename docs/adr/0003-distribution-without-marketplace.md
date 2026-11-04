# ADR 0003: Distribute with install scripts and a notarized Mac package, not Microsoft Marketplace

- Status: accepted
- Date: 2026-11-04

## Context
SlideMarks is free, and the project spends no money on distribution: no paid domain, accounts or certificates. Users need two things: the font, and the Office add-in (an XML manifest that Word and PowerPoint must be told about). Manual sideloading meant copying a file into hidden folders on Mac, or setting up a shared folder and a Trust Center catalog on Windows.

The options we checked:
- **Microsoft Marketplace** (one-click add-in install from inside Office) needs a Partner Center account in the *Microsoft 365 and Copilot* program. That requires a work or school (Entra ID) account and business verification; individual accounts can't enroll. It also commits the add-in to every platform in review, including Office on the web, where a locally installed font may not render. It would not install the font either.
- **Microsoft Store** (free for individuals; Microsoft signs MSIX packages) can't register the add-in. Packaged apps' HKCU registry writes are virtualized, and turning that off needs the restricted `unvirtualizedResources` capability, meant for certain games. Shared fonts also need Store approval. The Store's EXE/MSI route needs the publisher's own code-signing certificate.
- **Windows code signing**: Azure Artifact Signing is paid and not open to individuals. SignPath Foundation is free for open source but expects an established project.
- **Mac**: the maintainer already has a paid Apple Developer account, so Developer ID signing and notarization cost nothing extra.

## Decision
- One step installs both the font and the add-in, per user, with no admin rights:
  - Mac: `SlideMarks.pkg` (Developer ID signed, notarized, attached to GitHub releases), or `curl … /install.sh | sh`.
  - Windows: `irm … /install.ps1 | iex`. Pasted commands aren't subject to SmartScreen or Gatekeeper, so they need no signing.
- The add-in is registered the way Microsoft's `office-addin-dev-settings` sideloads it: the `wef` folder inside each app's container on Mac, and `HKCU\Software\Microsoft\Office\16.0\WEF\Developer` on Windows.
- Office on the web and organizations keep the manifest-based routes (Upload My Add-in, Microsoft 365 admin center).

## Consequences
- **Developer add-ins:** Office lists SlideMarks under "Developer Add-ins". The registration mechanisms aren't a supported end-user API, and Microsoft could change them.
- **macOS prompt:** on macOS 14 and later, writing into Office's container prompts "would like to access data from other apps". The installers explain this and report a refusal instead of failing silently.
- **Updates:** the add-in itself updates automatically, since it loads from GitHub Pages. The font updates only when users re-run the installer.
- **Windows signing:** a signed Windows installer can follow if SignPath accepts the project.
- **Revisit:** reconsider Marketplace if Microsoft opens the Microsoft 365 and Copilot program to individual accounts.
