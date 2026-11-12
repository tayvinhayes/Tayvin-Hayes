# Biojacked 1.0: App Store launch kit

The app itself lives in the Biojacked artifact (version 18 has these changes). This folder holds the pieces that need to live somewhere public or get pasted into App Store Connect.

## What changed in the app

| Change | Why it matters |
|---|---|
| **Try before signing up.** "Start your build, free" and coach-code joins now run the whole onboarding, including the 3D sculpt, with no account. Email comes last, on a "Save your build" screen that shows their build and matched program. | The old flow asked a stranger for an email and a 6-digit code before they saw anything. That's where most downloads quit. |
| **App Review sign-in.** One configured demo email signs in with a password instead of an emailed code. | Reviewers can't receive your codes. "We were unable to sign in" is a common rejection for code-only apps (Guideline 2.1). |
| **Privacy Policy, Terms, Support** in the front-page fine print, on the sign-up screens, in member Profile and in coach Settings. They open inside the app with a Back button. | Required in-app (Guideline 5.1.1). |
| **AI permission prompt** before the first "Describe a meal" estimate. | Apple now requires explicit permission before personal data goes to a third-party AI (Guideline 5.1.2). |
| **Ratings prompt** after a session with a new best or a medal, never in someone's first 3 days or before their 3rd session, at most every 120 days. | Early ratings drive ranking and conversion on the store page. |

## Before you submit, in order

1. **Fill the placeholders** in `privacy.html` and `terms.html`: `[YOUR SUPPORT EMAIL]` (both files) and `[YOUR STATE]` (terms). Read both pages and have someone qualified check them. They're drafts built from what the app really collects.
2. **Host the two pages publicly.** App Store Connect needs a public Privacy Policy URL. If GitHub Pages is on for this repo, merging this branch puts them at
   `https://tayvinhayes.github.io/Tayvin-Hayes/biojacked/privacy.html` and `.../terms.html`.
3. **In the app's `index.html`, set the config at the top of the main script:**
   - `BJ_CLOUD.review`: the demo email you'll give Apple.
   - `BJ_LEGAL.support`: your support email (shows a "Contact support" row).
   - Leave `BJ_LEGAL.privacy` and `terms` as `privacy.html` / `terms.html` if those files ship inside the app bundle, or point them at the hosted URLs.
4. **Create the demo user** in Supabase: Authentication, Users, Add user, with that email and a password. Sign in once yourself and run through Start free so the account has a program and some data.
5. **Add the ratings plugin** to the iOS project:
   `npm install @capacitor-community/in-app-review && npx cap sync ios`
   Without it the prompt does nothing; nothing breaks.
6. **Check the AI provider.** The permission prompt and privacy policy name Anthropic's Claude, matching the "Claude's estimates" label in the Food tab. If your `food-ai` edge function calls a different provider, change both.
7. **Copy the new files into the Capacitor web folder** (`index.html`, `privacy.html`, `terms.html`), then `npx cap copy ios` and build.
8. **Test on a real iPhone:** Start free → sculpt → Save my build with a real email; sign in with the demo account; Describe a meal (permission prompt shows once); open Privacy and Terms from Profile; Delete account.

## App Store Connect

**Name** (25/30): `Biojacked: Physique Coach`

**Subtitle** (30/30): `Build the body you want, in 3D`

**Promotional text** (152/170):
> Sculpt the physique you want on a 3D body, get the program built for it, and log every set, meal and win. Free to start. A real coach when you want one.

**Keywords** (94/100, no spaces after commas, don't repeat words from the name):
```
workout,gym,lifting,bodybuilding,macro,calorie counter,meal tracker,program,ffmi,strength,diet
```

**Category:** Health & Fitness (primary). Lifestyle (secondary, optional).

**Description:**
> Most apps ask what you weigh. Biojacked asks what you want to look like.
>
> SCULPT YOUR GOAL IN 3D
> Pick the physiques you're after, from lean athlete to classic, hourglass to strong. Then turn a 3D body and choose exactly which muscles to grow and how much. Biojacked checks it against your frame and natural limits, so the goal is ambitious and real.
>
> GET THE PROGRAM BUILT FOR IT
> Your program is matched to the build you chose. Every session shows last time's numbers and today's target, with a rest timer and new bests called out as you hit them.
>
> EAT FOR IT WITHOUT THE SPREADSHEET
> Search 7,600 foods, scan a barcode, or just describe your meal and let AI estimate it. You check every number before it's logged. Daily targets adjust to your goal and your training.
>
> CLOSE YOUR RINGS
> Train, Fuel and Habit, every day. Build streaks, earn medals, and see your team's wins on the feed.
>
> A REAL COACH WHEN YOU WANT ONE
> Train free for as long as you like. When you want more, apply for one-on-one coaching: weekly check-ins with written feedback, calls, and a program adjusted as you progress.
>
> FOR COACHES
> Run your whole coaching business from one app your clients will actually open: programs, food diaries, check-ins, call booking, challenges and messages, under your business name. Free for your first two clients.
>
> Biojacked provides coaching, not medical advice. Talk to a doctor before starting a new training or nutrition plan.

**Privacy Policy URL:** the hosted `privacy.html` from step 2. **Support URL:** a page or `mailto:` with your support email.

**App Privacy (nutrition label).** Everything is linked to the user, used for App Functionality, and **not** used for tracking:
- Contact Info: Email Address, Name
- Health & Fitness: Health, Fitness
- User Content: Photos or Videos, Other User Content
- Identifiers: User ID
- Purchases: Purchase History (coach plans, bought on the web)

Nothing in Diagnostics, Location, Contacts or Usage Data: the app has no analytics or crash-reporting SDK. If you add one, update this.

**Age rating:** answer the questionnaire honestly. The Terms say 16+, so make sure the two agree.

### Screenshots: six frames, in this order

Required size: 6.9" (1320 × 2868 or 1290 × 2796). The first two frames do most of the selling, because they're all most people see in search results.

1. **3D sculpt step**, a focus muscle being dialed up. Caption: *Sculpt the body you want. In 3D.*
2. **Build picker** with 2–3 builds ranked. Caption: *Pick your physique. Get the program for it.*
3. **Workout logging** with a "New best" showing. Caption: *Every set. Every new best.*
4. **Food: Describe a meal** results. Caption: *Say what you ate. Macros done.*
5. **Today: the week dial and rings.** Caption: *Close your rings. Earn medals.*
6. **Coaching or check-in feedback.** Caption: *A real coach in your corner.*

### App Review notes (paste this, filling in the password)

> Demo account: review@[your domain] / [password]. On the first screen, tap Sign in, enter the email, and the app asks for the password (all other accounts sign in with an emailed 6-digit code).
>
> You can also try the app without an account: tap "Start your build, free". The account is only created at the end, when you save your build.
>
> Payments: nothing is sold in the iOS app. Coaches subscribe to Biojacked plans on our website; the iOS app hides plans and prices from coaches (Guideline 3.1.3(f)). Members can apply for one-on-one coaching from an independent coach, which includes live calls; the coach arranges payment with the member directly, and the app contains no purchase links or buttons (Guideline 3.1.3(d), person-to-person services).
>
> AI: "Describe a meal" (Food tab) sends only the meal text and optional photo to Anthropic's Claude to estimate nutrition, after an in-app permission prompt.
>
> Account deletion: Profile (avatar, top right) → Delete account. Coaches: Settings → Delete account.
>
> The team feed shows only wins the app generates automatically (finished sessions, new bests, medals). Members can't post text to other members.

## For 1.1, after launch

- **Apple Health sync** for steps, weight and workouts. It removes the manual Steps log and is the most-requested integration for iPhone fitness apps.
- **Sign in with Apple** next to email, for one-tap sign-up.
- **Sculpt-first onboarding**: open on the 3D builds and move the name and weight form to the end.
- **Home Screen widget** for today's rings, and a **Live Activity** for the rest timer.
