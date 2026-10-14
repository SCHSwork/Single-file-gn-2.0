# Host your own GN 2.0 — setup guide

This folder has everything you need to run your own copy of GN 2.0:

| File | What it is |
|---|---|
| `index.html` | The whole site in one file. This is what you host. |
| `firestore.rules` | Security rules you paste into Firebase (step 3). |
| `SETUP.md` | This guide. |

Your copy is completely separate from the original GN 2.0. It has **no Firebase project built in** and **doesn't follow the original site's owner settings**, so nothing the original owner does can lock, change or shut down your site.

**How long it takes:** about 5 minutes for games only (Part A), about 20 minutes with accounts (Parts A–C).

**What you need:** a computer, a text editor (Notepad on Windows, TextEdit on Mac, or VS Code) and a Google account for Firebase. It's all free.

---

## Contents

- [Part A — Put the site online](#part-a--put-the-site-online) (required)
- [Part B — Create a Firebase project](#part-b--create-a-firebase-project) (for accounts)
- [Part C — Connect your site to Firebase](#part-c--connect-your-site-to-firebase) (for accounts)
- [Part D — Make yourself an admin](#part-d--make-yourself-an-admin) (optional)
- [Part E — Turn on the Owner Panel](#part-e--turn-on-the-owner-panel) (optional)
- [Updating your copy](#updating-your-copy)
- [Troubleshooting](#troubleshooting)
- [Firebase free limits](#firebase-free-limits)

---

## Part A — Put the site online

### A1. Download the file

1. Open `index.html` in this folder on GitHub.
2. Click the **Download raw file** button (the ⬇ arrow, top right of the file).
3. Save it somewhere you'll find it, like your Desktop. Keep the name `index.html`.

> The file is about 1.4 MB. GitHub won't show it as a preview, and that's normal.

You can double-click the file now to try it. The games work right away, but you can't sign in yet.

### A2. Pick a host

Use **one** of these. All of them are free.

#### Option 1: Netlify Drop (easiest, no account to start)

1. Go to **app.netlify.com/drop**.
2. Drag the **folder** containing `index.html` onto the page. Put only `index.html` in that folder.
3. You get a link like `https://random-name-123.netlify.app`. That's your site.
4. Create a free Netlify account when it asks. Otherwise the site is deleted after an hour.
5. To change the name: **Site configuration → Change site name.**

To update the site later: open the site in Netlify, go to **Deploys**, and drag the folder in again.

#### Option 2: GitHub Pages

1. Sign in to GitHub and click **+ → New repository**.
2. Name it anything (for example `games`), set it to **Public**, and click **Create repository**.
3. Click **uploading an existing file**, drag in `index.html`, then click **Commit changes**.
4. Go to **Settings → Pages**. Under **Branch**, pick `main` and `/ (root)`, then click **Save**.
5. Wait 1–2 minutes and refresh. Your link appears at the top: `https://your-name.github.io/games/`.

To update the site later: upload the new `index.html` to the repo again. It replaces the old one.

#### Option 3: Cloudflare Pages, Vercel or Neocities

These all work the same way: create a project and upload `index.html` as a static site, with no build settings.

✅ **Checkpoint:** open your link. You should see the GN 2.0 home page with games. If you only want games, you're done. Keep going to add accounts.

---

## Part B — Create a Firebase project

Firebase is Google's free service that stores accounts and saves. You make your own project, so your players' data is yours.

### B1. Create the project

1. Go to **console.firebase.google.com** and sign in with a Google account.
2. Click **Create a project** (or **Add project**).
3. Enter a name, like `my-games`, and click **Continue**.
4. **Turn off Google Analytics.** The site doesn't use it. Then click **Create project**.
5. Wait for it to finish, then click **Continue**.

### B2. Turn on sign-in

Players only ever type a username and password. Behind the scenes, the site turns the username into a made-up email (`name@gnmath.local`), so it uses Firebase's **Email/Password** sign-in.

1. In the left menu, open **Build → Authentication** (it may be under **Security**). Click **Get started**.
2. Open the **Sign-in method** tab.
3. Click **Email/Password**.
4. Turn on the **first** switch (Email/Password). Leave "Email link" **off**.
5. Click **Save**.

### B3. Create the database

1. In the left menu, open **Build → Firestore Database** and click **Create database**.
2. Choose **Standard edition** if it asks.
3. **Location:** pick one close to your players, like `us-central` or `nam5` for the US. You **can't change this later**.
4. Choose **Start in production mode** and click **Create**.

---

## Part C — Connect your site to Firebase

### C1. Paste in the security rules

The rules decide who can read and change what. For example, only you can see your own saves, and each person can vote once per game. **Without them, accounts won't work.**

1. Open `firestore.rules` in this folder on GitHub and click the **Copy raw file** button (two squares, top right).
2. In Firebase, go to **Firestore Database → Rules**.
3. Select everything in the editor, delete it, and paste.
4. Click **Publish**.

### C2. Get your Firebase config

1. Click the **gear icon** next to "Project Overview" (top left), then **Project settings**.
2. Scroll down to **Your apps** and click the **`</>`** (Web) button.
3. Enter a nickname, like `site`. **Don't** check "Firebase Hosting". Click **Register app**.
4. Firebase shows some code. Find the part that looks like this and copy only the `{ ... }` with everything inside it:

```js
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "my-games-ab12c.firebaseapp.com",
  projectId: "my-games-ab12c",
  storageBucket: "my-games-ab12c.firebasestorage.app",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abc123def456"
};
```

5. Click **Continue to console**.

You can always find this again under **Project settings → Your apps**.

> **Is it safe to put this in a public file?** Yes. Every Firebase website has this config in its page. It only says *which* project to talk to. What players can actually do is controlled by the rules you published in C1.

### C3. Put the config in `index.html`

1. Open your downloaded `index.html` in a text editor.
   - **Windows:** right-click → **Open with → Notepad**
   - **Mac:** open **TextEdit**, then **File → Open**. If it shows a web page instead of code, go to **TextEdit → Settings → Open and Save** and check **Display HTML files as HTML code**.
   - Don't edit it on GitHub's website. The file is too big for GitHub's editor.
2. Near the very top (about line 11) you'll find this block. Use **Ctrl+F** (Mac: **Cmd+F**) and search for `GN_CONFIG`:

```js
window.GN_CONFIG = {
    // ...comments...
    firebase: null,

    // ...comments...
    settingsRepo: ""
};
```

3. Replace `null` with the `{ ... }` you copied. **Keep the comma after the closing `}`.** It should look like this:

```js
window.GN_CONFIG = {
    firebase: {
        apiKey: "AIzaSy...",
        authDomain: "my-games-ab12c.firebaseapp.com",
        projectId: "my-games-ab12c",
        storageBucket: "my-games-ab12c.firebasestorage.app",
        messagingSenderId: "123456789012",
        appId: "1:123456789012:web:abc123def456"
    },

    settingsRepo: ""
};
```

4. Save the file. Make sure it's still named `index.html`, not `index.html.txt`.
5. Upload it to your host again (see [A2](#a2-pick-a-host)).

### C4. Test it

1. Open your site's link. Refresh with **Ctrl+Shift+R** (Mac: **Cmd+Shift+R**) so you get the new version.
2. A **person icon** should now be in the header, next to the ⚠ button.
3. Click it and create an account.
4. Play a game for a minute, then close it. Your progress is saved to the cloud.
5. To check: in Firebase, go to **Authentication → Users**. Your account should be listed there.

✅ **Checkpoint:** accounts, cloud saves, 👍/👎 ratings, broken-game reports, "Submit a game" and the online counter all work now.

---

## Part D — Make yourself an admin

Admins get an **Admin Panel**. From there they can review submitted games, see accounts, suspend people, mark trusted reporters and make other accounts admins. Firebase adds the first admin by hand. After that, you can add more from the site.

1. On your site, sign in to the account that should be admin.
2. In Firebase, go to **Authentication → Users** and copy that account's **User UID**. It's a long code like `AKOZ92Fya7dXqNDcSFl8T6nLHwn2`. Hover over it to see a copy button.
3. Go to **Firestore Database → Data** and click **+ Start collection**.
4. **Collection ID:** type `admins` (all lowercase) and click **Next**.
5. **Document ID:** paste your **User UID**. Don't click "Auto-ID".
6. Add one field: **Field** `name`, **Type** `string`, **Value** your username.
7. Click **Save**.
8. Back on your site, refresh the page, then open the person icon → **🛡️ Admin Panel**.

> If the Admin Panel says your account isn't an admin, it shows the exact ID it expects. Check that it matches the document ID you created.

---

## Part E — Turn on the Owner Panel

The **Owner Panel** (Settings → Owner Panel) controls the whole site for everyone:

- lock the site or show a "closed" screen
- show an announcement banner or a message of the day
- disable individual games
- set the default theme, card size and sort order for new visitors
- add footer links

It saves these settings as a file in a **GitHub repo of yours**. Owner access works like a password: only someone with a GitHub token that can edit that repo gets in. **Skip this part if you don't need it.** The Owner Panel stays locked until you set it up.

### E1. Pick a repo

Use the repo hosting your site (if you used GitHub Pages), or create a new one. It can be private. You don't need to add any files. The site creates `config/owner-settings.json` the first time you save.

### E2. Add it to `index.html`

In the `GN_CONFIG` block, set `settingsRepo` to `your-github-name/repo-name`:

```js
    settingsRepo: "your-github-name/games"
```

Save the file and upload it again.

### E3. Make a GitHub token

1. On GitHub, click your profile picture → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. **Name:** `GN owner panel`. **Expiration:** your choice. When it expires, you just paste a new one.
3. **Repository access:** **Only select repositories**, then pick the repo from E1.
4. **Permissions → Repository permissions → Contents:** **Read and write**.
5. Click **Generate token** and copy it. It starts with `github_pat_`. GitHub only shows it once.

### E4. Unlock it

1. On your site, open **Settings** (gear icon) → **Owner Panel**.
2. Paste the token and click **Unlock**.

The token is checked with GitHub and saved **only in that browser**. Never post it anywhere. Anyone who has it can edit that repo.

Changes you make in the Owner Panel reach every visitor within a few minutes.

---

## Updating your copy

The original GN 2.0 keeps getting new games and fixes, and this folder is rebuilt automatically when it does. To update:

1. Open your current `index.html` and **copy your whole `GN_CONFIG` block**.
2. Download the new `index.html` from this folder.
3. Open it, replace its `GN_CONFIG` block with yours, and save.
4. Upload it to your host.

Your accounts, saves and settings live in your Firebase and your GitHub repo, not in the file, so nothing is lost when you update.

> **Tip:** if Firebase changed something, paste `firestore.rules` into Firebase again (C1) after updating. It doesn't hurt to do it every time.

---

## Troubleshooting

**The person icon (account button) doesn't appear**
- You're seeing an old copy. Refresh with **Ctrl+Shift+R** and wait a minute after uploading.
- There's a typo in `GN_CONFIG`. Check for a missing comma after the closing `}` of `firebase`, or quotes that got turned into curly quotes (“ ”). TextEdit and Word do this, so use plain quotes `"`. To check: press **F12** on your site → **Console** and look for a red error near the top.

**"Accounts failed to start" or sign-in errors**
- `auth/operation-not-allowed`: Email/Password isn't turned on (B2).
- `auth/configuration-not-found`: you never clicked **Get started** in Authentication (B2).
- `auth/api-key-not-valid` or `invalid-api-key`: the `apiKey` was copied wrong (C2–C3).
- Your school or network blocks `gstatic.com` or `googleapis.com`. Accounts need both.

**"Missing or insufficient permissions"**
- The rules weren't published, or not all of them were pasted. Redo C1 and make sure you clicked **Publish**.

**The Admin Panel says I'm not an admin**
- The collection must be named exactly `admins`, and the document ID must be your **User UID**, not your username (Part D). Refresh the site after adding it.

**Owner Panel: "That token can't access…" or "isn't allowed to edit…"**
- `settingsRepo` is misspelled, or the token wasn't given that repo with **Contents: Read and write** (E3).
- If it names `SCHSwork/math`, then `settingsRepo` is still empty. Set it (E2) and upload again.

**Everything worked, then stopped for the rest of the day**
- You probably hit Firebase's free daily limit. See below. It resets every night (Pacific time).

---

## Firebase free limits

The free **Spark** plan needs no credit card. Its main limits are:

| | Free each day / total |
|---|---|
| Database reads | 50,000 per day |
| Database writes | 20,000 per day |
| Database storage | 1 GB total |
| Accounts | effectively unlimited for username sign-in |

That's plenty for a site with a few hundred regular players. Cloud saves are the biggest use of storage, since some games keep large saves. Watch **Firestore Database → Usage** in Firebase. If you outgrow the free plan, you can switch to **Blaze** (pay as you go). Firebase never charges you unless you switch to Blaze yourself.

---

## Optional extras

- **Lock your config to your site:** in **console.cloud.google.com → APIs & Services → Credentials**, open the "Browser key (auto created by Firebase)" and add your site's address under **Website restrictions**, for example `https://my-games.netlify.app/*`. Then other sites can't use your Firebase project. After this, opening the file straight from your computer won't be able to sign in.
- **Rename your site:** the name "GN 2.0" appears in the header logo, the page title and a few messages. Use your editor's **Find & Replace** to change `GN 2.0` to your own name. Do this *outside* the `GN_CONFIG` block, and redo it each time you update.
- **Why the tab says "Dashboard":** the site disguises its browser tab as Canvas by default (the tab cloak). Players can change or turn this off in **Settings**.
