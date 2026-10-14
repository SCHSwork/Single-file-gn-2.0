# Host your own GN 2.0

`index.html` in this folder is the whole GN 2.0 site in one file, ready for you to host with **your own** Firebase. Nothing in it is tied to the original site: it has no Firebase project built in, and it doesn't take orders from the original site's owner settings.

It works as-is with no setup at all: just games, without accounts. Follow the steps below only if you want accounts, cloud saves, ratings and broken-game reports.

## 1. Host the file

Put `index.html` on any static host:

- **Netlify Drop**: go to app.netlify.com/drop and drag the file in
- **GitHub Pages**: make a repo, upload `index.html`, then Settings → Pages → deploy from `main`
- **Cloudflare Pages, Vercel, Neocities**: all work too

## 2. Make a Firebase project (free)

1. Go to [console.firebase.google.com](https://console.firebase.google.com) → **Add project**. Analytics isn't needed.
2. **Build → Authentication → Get started → Sign-in method → Email/Password → Enable → Save.**
   Players only ever type a username; the site turns it into a made-up email behind the scenes.
3. **Build → Firestore Database → Create database.** Pick a location near your players and start in **production mode**.
4. Open the **Rules** tab, delete what's there, paste in all of `firestore.rules` from this folder, then click **Publish**.
5. **Project settings** (gear icon) → **Your apps** → the **</>** (Web) button. Give it any name and skip Hosting. Copy the `firebaseConfig` it shows you.

## 3. Paste your config into the file

Open `index.html` in a text editor. Near the very top is the only part you need to edit:

```js
window.GN_CONFIG = {
    firebase: null,
    settingsRepo: ""
};
```

Replace `null` with your config:

```js
window.GN_CONFIG = {
    firebase: {
        apiKey: "AIza...",
        authDomain: "your-project.firebaseapp.com",
        projectId: "your-project",
        storageBucket: "your-project.firebasestorage.app",
        messagingSenderId: "1234567890",
        appId: "1:1234567890:web:abc123"
    },
    settingsRepo: ""
};
```

Save the file and upload it again. The account button now appears in the header.

The Firebase config is meant to be public. Your data is protected by the rules you pasted in step 2, not by hiding the config.

## 4. Make yourself an admin (optional)

Admins can review game submissions, manage accounts and suspend people.

1. Create an account on your site.
2. In Firebase: **Authentication → Users**. Copy your account's **User UID**.
3. **Firestore Database → Start collection.** Use `admins` as the collection ID and your UID as the document ID. Add any field (for example `name` = your username), then click **Save**.

From then on, admins can make other accounts admins from the site's admin panel.

## 5. Owner panel (optional)

The owner panel can lock the site, show announcements, disable games and set defaults for visitors. It saves those settings as a file in a GitHub repo of yours:

1. Make a GitHub repo (it can be the one hosting your site) with a file at `config/owner-settings.json` containing `{}`.
2. Set `settingsRepo: "your-name/your-repo"` in `GN_CONFIG`.
3. On the site, open the owner panel and give it a GitHub token that can edit that repo.

Leave `settingsRepo` empty and this feature stays off.

## Updating

This file is rebuilt from the original GN 2.0 automatically. To update your copy, download the new `template/index.html` and copy your `GN_CONFIG` block into it. That block is the only part you changed.
