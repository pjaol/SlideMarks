# SlideMarks for Office — making the font genuinely easy to use

I'd build a single Office add-in with a Character Map-style task pane, shared across Word, PowerPoint, and Excel.

The user experience would be simple: open SlideMarks from the Office ribbon, search or browse symbols, click one, and have it inserted at the cursor or into the selected cell.

We can make most of this work using Office.js, without needing a native installer, account, or subscription.

There is one significant exception: automatically embedding the font into the currently open document. That needs a different approach, because Office.js does not expose a general API to turn on font embedding.

## 1. The interface I'd build

Here's a functional concept of the picker. It uses ordinary placeholder symbols for now; the actual add-in would render the existing SlideMarks font.

## SlideMarks

Office symbol picker · Concept

All symbols

○0%

◔25%

◑50%

◕75%

●100%

→Right arrow

←Left arrow

↑Up arrow

↓Down arrow

✓Check

✕Cross

↗Rising

↘Falling

## ◕

Harvey 75%

U+E003 · Harvey balls

Font: SlideMarks Regular

Replace selection / selected cell

Append to existing text

&#x20;Copy symbolThe real add-in's primary action would be Insert, targeting the active Office document. This preview copies the character instead.

Font sharing: embedding is controlled by Office or a document export workflow.

This would be a permanent, resizable side panel, not a modal dialog. The ribbon would contain a SlideMarks button that opens it.

A task pane is supported across the three Office applications, and Microsoft supports shared runtimes and optional keyboard shortcuts in these add-ins.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com\&sz=32)

Microsoft Learn+1



## 2. How insertion would work in each application

This is where I'd keep the UI shared but use different Office adapters.

| Application               | How we insert                                             | Feasibility      |
| ------------------------- | --------------------------------------------------------- | ---------------- |
| Word                      | Insert character at selection and apply SlideMarks font   | Excellent        |
| Excel                     | Write character to selected cell and set font name        | Excellent        |
| PowerPoint text boxes     | Insert/replace selected text, then format where supported | Requires testing |
| PowerPoint existing table | Update cell text; font formatting is API-dependent        | Main challenge   |

### Word

Word has the cleanest implementation. We can insert a character and format only the inserted range.

```
await Word.run(async (context) => {
  const selection = context.document.getSelection();
  const inserted = selection.insertText(
    String.fromCodePoint(0xE003),
    Word.InsertLocation.replace
  );

  inserted.font.name = "SlideMarks";
  await context.sync();
});
```

That can work within ordinary document text and table-cell contents.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com\&sz=32)

Microsoft Learn



### Excel

Excel provides direct access to the selected range and its font.

```
await Excel.run(async (context) => {
  const range = context.workbook.getSelectedRange();

  range.values = [[String.fromCodePoint(0xE003)]];
  range.format.font.name = "SlideMarks";

  await context.sync();
});
```

For the MVP, limit this to one selected cell and warn before overwriting a nonempty cell. Excel also supports alignment, font sizing, and colors through the range API.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com\&sz=32)

Microsoft Learn+1



### PowerPoint

PowerPoint is the one I'd prototype first, because your original use case was inserting Harvey balls directly into comparison tables.

Microsoft's documented PowerPoint table APIs can change the text of existing cells, but have limitations around changing their formatting. New tables offer more formatting control, including cell font settings.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com\&sz=32)

Microsoft Learn+1



I'd test two paths:

- Selection-based text insertion: insert into the current text selection, ideally preserving existing cell formatting.
- Table-cell insertion: identify the active table cell and update its content, retaining or applying SlideMarks if possible.

We should not build the rest of the add-in on an assumption that arbitrary PowerPoint table text can always be inserted and formatted exactly as we want.

## 3. The font embedding button — the difficult part

Here's what I'd like the user to see:

Document font status

SlideMarks Regular

Verification needed

Prepare document for sharing

Preserve SlideMarks symbols when others open the file.

&#x20;View embedding instructionsConcept only. An Office.js add-in cannot directly enable the native font-embedding setting.

### Can Office.js embed the font?

Not directly. I couldn't find a supported Office.js API that enables font embedding or adds a font to the document's embedded-font collection.

Microsoft documents font embedding as an application-level save option in Word and PowerPoint, not as an Office.js setting.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://support.microsoft.com\&sz=32)

Microsoft Support



We do have some alternatives.

| Approach                | Behavior                                                    | Recommendation                            |
| ----------------------- | ----------------------------------------------------------- | ----------------------------------------- |
| Office.js only          | Guide users to Office's native embed-font setting           | MVP                                       |
| Native desktop helper   | Modify a saved Office document to embed SlideMarks          | Potential future option                   |
| Document export service | Generate a new `.docx` or `.pptx` containing embedded fonts | Useful, but extra workflow                |
| VBA/COM automation      | Control supported desktop functionality on Windows          | Platform-specific; investigate separately |

Your existing Python build already contains `office_fonts.py`, which generates embedded fonts for Word and PowerPoint specimen files.

That is particularly interesting. We could eventually reuse the existing embedding code in a local document-processing helper, rather than inventing another font-embedding implementation.

But it would work on a saved file, not transparently modify the open document through Office.js. We would also need to preserve all document content and relationships, avoid damaged files, and handle concurrent editing and cloud-synchronized documents.

I'd avoid promising a one-click Embed Font button until we prove a safe way to operate on the active document.

Instead, the MVP can provide an Embedding Guide action, and the add-in can eventually offer a separate Prepare a Shareable Copy workflow.

Also, Excel deserves separate treatment: standard `.xlsx` files don't offer the same conventional custom-font embedding workflow as Word and PowerPoint. For recipients without the font, a PDF or vector fallback may be required.

## 4. Architecture: one interface, three adapters

I would add a TypeScript workspace alongside your existing Python font generator.

Existing SlideMarks source

`source/symbols.json` + glyph definitions

Generated catalog package

Glyph names, families, code points, keywords, previews

Shared Office task pane

Search · Filters · Favorites · Preview · Insert

Word

Text ranges

PowerPoint

Shapes / cells

Excel

Cell ranges

Suggested repository additions:

```
SlideMarks/
├── source/                  # Existing glyph source
├── src/slidemarks_build/    # Existing Python generator
├── dist/                    # Existing generated assets
│
├── packages/
│   ├── catalog/             # Generated JSON/TypeScript data
│   └── office-core/         # Shared picker logic
│
├── apps/
│   └── office/
│       ├── taskpane/        # Shared React/TypeScript UI
│       ├── adapters/
│       │   ├── word.ts
│       │   ├── powerpoint.ts
│       │   └── excel.ts
│       └── manifests/
│
└── tests/
    └── office/
```

A single task pane can switch behavior based on its host application. Whether we ship one multi-host manifest or separate app-specific manifests can be decided when packaging.

## 5. How people would install it

I'd make the Office add-in available from the SlideMarks website, with a straightforward install route.

For initial development, sideloading is enough. Eventually, distribution through Microsoft's add-in marketplace is worth considering so users don't need to handle manifests manually.

There is a distinction between installing the add-in and installing the font: the add-in can't simply install the TTF onto the user's operating system. The desktop font must still be installed separately, or the document must have a compatible embedded copy.

That means installation should be presented as two clearly explained components: SlideMarks Font and SlideMarks Office Picker.

## 6. Implementation order

I would prioritize based on the riskiest integration, not the easiest one.

1. PowerPoint insertion proof of concept

   Test plain text shapes and existing table cells on Mac and Windows. Determine whether insertion and font assignment can be done without changing other cell formatting.
2. Shared Character Map picker

   Search, family filtering, favorites, recent symbols, character previews, keyboard navigation, and copy/insert actions.
3. Word and Excel adapters

   Implement cursor and cell insertion using their established text/font APIs.
4. Sharing and embedding assistance

   Provide native Office instructions first; separately prototype preparing a new embedded-font copy using the existing Python embedding logic.
5. Distribution

   Package the add-in for Windows, macOS, and supported Office web clients, with appropriate feature detection.

The most important design choice is that the picker should be completely independent of Office.js. It should work as the same searchable character map on the SlideMarks website, with a thin Office adapter providing the Insert action.

That way we develop the search and symbol experience once, rather than maintain separate character maps for three applications.

I'd begin by proving PowerPoint's existing-table insertion and formatting behavior. If that works reliably, the rest is largely conventional Office add-in engineering. If it doesn't, we'll know early enough to design a credible fallback rather than compromise the core reason SlideMarks exists.



--
Yes. We should treat distribution and installation as a core part of SlideMarks, rather than assume that a working Office.js add-in on your development machine is ready for other users.

I'd design it so someone can visit the SlideMarks website, install the font, add SlideMarks to Office, and start inserting symbols without touching GitHub, Node, Python, or a developer console.

There are actually three separate things to distribute:

1. The SlideMarks font — installed on the computer.
2. The SlideMarks Office add-in — installed into Word, PowerPoint, and Excel.
3. The SlideMarks task-pane application — hosted centrally and loaded by Office.

## 1. How it would work for an ordinary user

## Get SlideMarks

Concept for the installation page

Step 1 — Install the font

Available for Windows, macOS, and Linux.

Download SlideMarks Font

Step 2 — Add to Microsoft Office

Install the symbol picker for Word, PowerPoint, and Excel.

Get the Office Add-in

Step 3 — Start using symbols

Open an Office document → SlideMarks → Search → Insert.

This is the desired production experience, not a currently published installation flow.

Microsoft explicitly supports publishing Office add-ins to its Marketplace and providing direct installation links from your own website. Those links can launch Word, PowerPoint, or Excel and initiate installation.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com\&sz=32)

Microsoft Learn



That gives us a realistic, native distribution path instead of asking users to sideload add-ins.

## 2. The deployment options

| Distribution method               | Intended audience | Recommendation           |
| --------------------------------- | ----------------- | ------------------------ |
| Local sideloading                 | Developers        | Development only         |
| Hosted manifest / test deployment | Beta testers      | Initial testing          |
| Microsoft Marketplace             | General public    | Primary production route |
| Microsoft 365 admin deployment    | Companies         | Enterprise support       |
| Native installer                  | Special cases     | Avoid initially          |

Microsoft 365 administrators can deploy add-ins to individual users, groups, or an entire organization. The add-in then appears in supported Office applications without each user installing it manually.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com\&sz=32)

Microsoft Learn+1



I'd aim for Microsoft Marketplace distribution from the beginning, while using test deployment before publication.

We should not make a downloadable manifest XML file the normal consumer installation experience.

## 3. Hosting: the add-in cannot depend on your development machine

Office.js add-ins are web applications running inside Office. The manifest tells Office where to load the user interface.

For development, that URL might be:

```
https://localhost:3000/taskpane.html
```

That is fine for you, but obviously fails when another person installs the add-in.

For production, we need something like:

```
https://office.slidemarks.org/taskpane.html
```

The actual domain is just illustrative.

SlideMarks public website

Downloads · Catalog · Installation help

Microsoft Marketplace

Office add-in listing and installation

SlideMarks hosted task pane

Static HTML · JavaScript · CSS · WOFF2

Word

PowerPoint

Excel

For this application, we shouldn't need a backend at all. The glyph catalog, search, preview, and Office insertion logic can run in the browser within the Office task pane.

I'd use static hosting such as Cloudflare Pages or GitHub Pages, with HTTPS and a custom domain. Microsoft requires HTTPS for Marketplace-published add-ins.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com\&sz=32)

Microsoft Learn+1



One caveat: the font can work offline after installation, but the hosted Office add-in will normally need connectivity to load. We should retain the standalone font and character map as the offline fallback.

## 4. Make installation independent of the developer setup

Here's the practical implementation model.

| Component          | Developer setup            | Production setup                |
| ------------------ | -------------------------- | ------------------------------- |
| Add-in manifest    | Local development manifest | Stable, published manifest      |
| Task pane          | Local dev server           | Public HTTPS hosting            |
| Font previews      | Locally generated WOFF2    | Bundled with hosted assets      |
| Desktop font       | Developer-installed TTF    | Downloadable installer/package  |
| Office integration | Sideload                   | Marketplace or admin deployment |
| Updates            | Manual rebuild             | Automated deployment            |
| User account       | None                       | None                            |

The important detail is that the hosted WOFF2 font only makes the add-in's own symbols render correctly. It does not install SlideMarks into Word or PowerPoint.

For insertion into Office documents, users still need the desktop font installed or appropriately embedded.

We should detect and explain that dependency rather than let an inserted symbol appear as an empty box.

## 5. Installation testing needs a clean-machine gate

This should become a release requirement, not just a one-time test.

Release acceptance checklist

Install without GitHub, Python, Node, or developer tools

Open the add-in from a different Microsoft 365 account

Load the task pane without localhost or developer services

Insert symbols in Word, PowerPoint, and Excel on supported clients

Verify missing-font behavior and installation guidance

Open a shared Word/PowerPoint file on a machine without SlideMarks

Verify that updates preserve old glyph code points

Confirm the published add-in works after a fresh Office restart

0 of 8 checks completed Copy checklist

I'd test at least one clean Windows environment and one clean Mac, plus Office on the web, before considering the add-in distributable.

We also need to account for Microsoft's platform-specific API support. A manifest can target Word, PowerPoint, and Excel, but the add-in should enable or disable features based on what the current Office client actually supports.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com\&sz=32)

Microsoft Learn



## 6. Add distribution to the repository now

I'd extend the current repository without disturbing the existing Python font generator.

```
SlideMarks/
├── source/
├── src/slidemarks_build/
├── dist/
│
├── packages/
│   ├── catalog/
│   └── office-core/
│
├── apps/
│   ├── website/
│   └── office/
│       ├── taskpane/
│       ├── adapters/
│       └── manifests/
│           ├── development.xml
│           └── production.xml
│
├── packaging/
│   ├── desktop/
│   └── releases/
│
└── .github/workflows/
    ├── build-font.yml
    ├── deploy-website.yml
    ├── deploy-office.yml
    └── release.yml
```

I'd use a stable production URL and separate preview deployments for testing. We should version the font, catalog, and add-in together, and never silently change a published character mapping.

Microsoft Marketplace certification also requires production information such as a support URL, privacy policy, and terms. Those should be part of the website before submission.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com\&sz=32)

Microsoft Learn



## 7. What I'd ship, in order

1. Public beta

   Host the Office task pane at a real HTTPS address. Produce a beta manifest that points to it, plus a downloadable font package. Test using a different machine and Microsoft account.
2. Public product website

   Make installation obvious, with separate font and Office add-in steps, examples, troubleshooting, and a searchable catalog.
3. Microsoft Marketplace publication

   Submit the add-in for certification. Once approved, replace manual sideloading with official installation links.
4. Enterprise deployment support

   Document installation through the Microsoft 365 admin center for organizations that restrict individual add-ins.

One thing I'd explicitly avoid: creating a custom `.exe` or `.pkg` just to install the Office add-in. That would introduce native installation, signing, updates, permissions, and platform-specific maintenance for something Microsoft already has a distribution mechanism for.

A standalone desktop font package is different; that's useful because fonts really do need to be installed at the operating-system level.

### My recommendation

The immediate engineering milestone should be:

Install SlideMarks from a hosted beta on a clean second machine, using a different Microsoft account, and successfully insert a symbol into a PowerPoint table.

That proves the entire chain: distribution, installation, font availability, Office integration, and user experience.

Once that works, making it publicly available through Microsoft's Marketplace becomes a packaging and certification exercise rather than a redesign of the product.