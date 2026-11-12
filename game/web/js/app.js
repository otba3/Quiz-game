(() => {
  const $ = (id) => document.getElementById(id);
  const stage = $("stage");

  const OUTPUT_DIR = "../../output/"; // question images live in output/images/
  const PER_GAME = 6; // questions per playthrough (fewer if the bank is smaller)
  const ORIGIN_PER_TYPE = 3; // Origin: 3 continent + 3 country questions
  const FEEDBACK_TIME = 3000; // milliseconds to show the result before the next question

  // Category buttons: key in QUIZ_DATA.categories -> label on screen, per language.
  const CATEGORIES = [
    { key: "year", name: { en: "Year of Creation", ar: "سنة الإنشاء" } },
    { key: "origin", name: { en: "Geographic Origin", ar: "الأصل الجغرافي" } },
  ];
  const UI = {
    en: {
      pick: "Choose a category",
      leaderboard: "Leaderboard",
      checkLeaderboard: "Check Leaderboard",
      daily: "Today",
      monthly: "This month",
      leaderboardBack: "Back to categories",
      leaderboardLoading: "Loading leaderboard...",
      leaderboardEmpty: "No scores yet.",
      leaderboardError: "Couldn't load the leaderboard. Please try again.",
      leaderboardRetry: "Try again",
      place: "Place",
      visitor: "User",
      leaderboardPoints: "Points",
      dailyProgress: (score, added) =>
        `Daily leaderboard: ${score}/12 (+${added} new question points).`,
      accountTitle: "Do you have an account code?",
      accountPrompt: "Enter it to save your quiz score to your account.",
      accountCodeLabel: "Account code",
      accountSubmit: "Use code and continue",
      accountGuest: "Continue as guest",
      accountCountdown: (seconds) =>
        `Guest mode starts in ${seconds} seconds.`,
      accountRequired: "Enter your account code, or continue as a guest.",
      accountTooLong: "The code must be 128 characters or fewer.",
      score: "Your score",
      again: "Play again",
      v: ["Try again.", "Well played.", "Perfect score."],
      savingTitle: "Saving your score...",
      savingMessage: "Saving this score under your account code.",
      savedTitle: "Score saved!",
      saved: "Your score is saved on this Pi under your account code.",
      guestTitle: "Playing as a guest",
      guestMessage: "Your score is shown but will not be saved to an account.",
      saveFailed: "We couldn't save your score. Please ask museum staff for help.",
      before: "Before",
      now: "Now",
      earned: (points) => `You earned ${points} points.`,
      pointsPending:
        "Quiz saved. Your points will be added after your second quiz in this category today.",
      thirdQuizPoints: (points) =>
        `On your third quiz, you earned ${points} extra points (half your score, rounded down). No more points in this category until tomorrow.`,
      dailyLimit:
        "Quiz saved. You have reached today's point limit for this category. You can earn points again tomorrow.",
      checkPoints: "Check Points",
      pointsTitle: "Your Points",
      historyTitle: "Points history",
      pointsBack: "Back to results",
      pointsNeeded: (balance) => `${balance} of 40 points. Keep going!`,
      rewardReady: "40 points reached! Ask museum staff about your reward.",
      earnedEntry: "Earned",
      redeemedEntry: "Reward redeemed",
      ratingTitle: "How would you rate your experience playing today?",
      ratingLabels: ["Very poor", "Poor", "Okay", "Good", "Excellent"],
      ratingSubmit: "Submit",
      ratingSkip: "Not now",
      ratingError: "We couldn't save your rating. Please try again.",
    },
    ar: {
      pick: "اختر فئة",
      leaderboard: "لوحة المتصدرين",
      checkLeaderboard: "تحقق من لوحة المتصدرين",
      daily: "اليوم",
      monthly: "هذا الشهر",
      leaderboardBack: "العودة إلى الفئات",
      leaderboardLoading: "جارٍ تحميل لوحة المتصدرين...",
      leaderboardEmpty: "لا توجد نتائج بعد.",
      leaderboardError: "تعذر تحميل لوحة المتصدرين. يُرجى المحاولة مرة أخرى.",
      leaderboardRetry: "حاول مرة أخرى",
      place: "المركز",
      visitor: "المستخدم",
      leaderboardPoints: "النقاط",
      dailyProgress: (score, added) =>
        `لوحة المتصدرين اليومية: ${score}/12 (+${added} نقاط لأسئلة جديدة).`,
      accountTitle: "هل لديك رمز حساب؟",
      accountPrompt: "أدخله لحفظ نتيجة الاختبار في حسابك.",
      accountCodeLabel: "رمز الحساب",
      accountSubmit: "استخدم الرمز وتابع",
      accountGuest: "المتابعة كزائر",
      accountCountdown: (seconds) =>
        `سيبدأ وضع الزائر خلال ${seconds} ثانية.`,
      accountRequired: "أدخل رمز حسابك أو تابع كزائر.",
      accountTooLong: "يجب ألا يتجاوز الرمز 128 حرفًا.",
      score: "نتيجتك",
      again: "العب مرة أخرى",
      v: ["حاول مرة أخرى.", "أحسنت.", "نتيجة كاملة."],
      savingTitle: "جارٍ حفظ نتيجتك...",
      savingMessage: "جارٍ حفظ النتيجة باستخدام رمز حسابك.",
      savedTitle: "تم حفظ نتيجتك!",
      saved: "تم حفظ نتيجتك على هذا الجهاز باستخدام رمز حسابك.",
      guestTitle: "اللعب كزائر",
      guestMessage: "ستظهر نتيجتك، ولكن لن يتم حفظها في حساب.",
      saveFailed: "تعذر حفظ نتيجتك. يُرجى طلب المساعدة من موظفي المتحف.",
      before: "قبل",
      now: "الآن",
      earned: (points) => `لقد حصلت على ${points} نقاط.`,
      pointsPending:
        "تم حفظ الاختبار. ستُضاف نقاطك بعد إكمال الاختبار الثاني في هذه الفئة اليوم.",
      thirdQuizPoints: (points) =>
        `حصلت على ${points} نقاط إضافية في الاختبار الثالث (نصف النتيجة بعد التقريب للأسفل). لا يمكن كسب المزيد في هذه الفئة حتى الغد.`,
      dailyLimit:
        "تم حفظ الاختبار. لقد وصلت إلى حد النقاط اليومي لهذه الفئة. يمكنك كسب النقاط مجددًا غدًا.",
      checkPoints: "تحقق من النقاط",
      pointsTitle: "نقاطك",
      historyTitle: "سجل النقاط",
      pointsBack: "العودة إلى النتيجة",
      pointsNeeded: (balance) => `${balance} من 40 نقطة. واصل التقدم!`,
      rewardReady: "وصلت إلى 40 نقطة! اسأل موظفي المتحف عن مكافأتك.",
      earnedEntry: "نقاط مكتسبة",
      redeemedEntry: "تم استبدال المكافأة",
      ratingTitle: "كيف تقيّم تجربتك في اللعب اليوم؟",
      ratingLabels: ["سيئة جدًا", "سيئة", "متوسطة", "جيدة", "ممتازة"],
      ratingSubmit: "إرسال",
      ratingSkip: "ليس الآن",
      ratingError: "تعذر حفظ تقييمك. يُرجى المحاولة مرة أخرى.",
    },
  };

  let lang = "en",
    category,
    questions,
    i,
    score,
    correctQuestionIds,
    accountCode = null,
    accountTimer = null,
    gameStartedAt,
    ratingScore = null,
    lastPointsResult,
    leaderboardCategory = "origin",
    leaderboardPeriod = "daily",
    leaderboardRequest = 0;

  const ACCOUNT_CODE_TIMEOUT_SECONDS = 30;

  // Pick the current language from an {en: ..., ar: ...} object; fall back to English.
  const tr = (obj) => obj[lang] || obj.en;

  function fit() {
    const s = Math.min(innerWidth / 1024, innerHeight / 600);
    stage.style.transform = "translate(-50%, -50%) scale(" + s + ")";
  }
  addEventListener("resize", fit);
  fit();

  function show(id) {
    stage.dataset.screen = id;
    document
      .querySelectorAll(".screen")
      .forEach((s) => s.classList.toggle("active", s.id === id));
  }

  // Returns a shuffled COPY of a list (Fisher-Yates shuffle), so the data is never changed.
  function shuffle(list) {
    const a = list.slice();
    for (let n = a.length - 1; n > 0; n--) {
      const r = Math.floor(Math.random() * (n + 1));
      [a[n], a[r]] = [a[r], a[n]];
    }
    return a;
  }

  // Like a deck of cards per category: questions not shown yet, in random order.
  // Every question is shown once before any question repeats.
  const decks = {};

  // Draw n questions from a deck. If it runs out, start a new shuffled deck
  // (without the questions just drawn) and take the rest from there.
  function draw(deckName, all, n) {
    const deck = decks[deckName] || [];
    const chosen = deck.slice(0, n);
    decks[deckName] = deck.slice(n);
    if (chosen.length < n) {
      const newDeck = shuffle(all.filter((q) => !chosen.includes(q)));
      const missing = n - chosen.length;
      chosen.push(...newDeck.slice(0, missing));
      decks[deckName] = newDeck.slice(missing);
    }
    return chosen;
  }

  // Choose this game's questions.
  function pickQuestions(key) {
    const all = QUIZ_DATA.categories[key];
    if (key === "origin") {
      const ofType = (type) =>
        draw(
          "origin-" + type,
          all.filter((q) => q.type === type),
          ORIGIN_PER_TYPE,
        );
      return shuffle(ofType("continent").concat(ofType("country")));
    }
    return draw(key, all, PER_GAME);
  }

  // Capitalise only the first letter on screen (Arabic has no capitals, so it is unchanged).
  const display = (text) => text.charAt(0).toUpperCase() + text.slice(1);

  // The question sentence in the current language, with {continent} and {year} filled in.
  function questionText(q) {
    const texts = QUIZ_DATA.texts[lang] || QUIZ_DATA.texts.en;
    const sentence =
      texts[q.question_key] || QUIZ_DATA.texts.en[q.question_key];
    const year = q.question_values ? q.question_values.year : "";
    return sentence
      .replace("{continent}", q.continent ? tr(q.continent) : "")
      .replace("{year}", year || "");
  }

  // Two JSON shapes exist:
  //   old (Origin): options = {en: [...], ar: [...]}, answer = {en, ar}, image = "..."
  //   new (Year):   options = [...],                  answer = "...",    images = [...]
  // These helpers turn both into the same form, so the rest of the code needs no ifs.

  // A list of options, each as {en, ar} (ar is missing for the new shape: tr() falls back to English).
  function optionsOf(q) {
    if (Array.isArray(q.options))
      return q.options.map((text) => ({ en: text }));
    return q.options.en.map((text, n) => ({
      en: text,
      ar: q.options.ar && q.options.ar[n],
    }));
  }

  // The correct answer as plain English text.
  const answerOf = (q) =>
    typeof q.answer === "string" ? q.answer : q.answer.en;

  // The picture paths as a list (1 or 2 pictures).
  const imagesOf = (q) => q.images || [q.image];

  function stopAccountTimer() {
    if (accountTimer !== null) clearInterval(accountTimer);
    accountTimer = null;
  }

  function continueAsGuest() {
    stopAccountTimer();
    accountCode = null;
    sessionStorage.removeItem("quizVisitor");
    showCategories();
  }

  function startAccountTimer() {
    stopAccountTimer();
    let remaining = ACCOUNT_CODE_TIMEOUT_SECONDS;
    const tick = () => {
      $("account-countdown").textContent = UI[lang].accountCountdown(remaining);
      if (remaining === 0) {
        continueAsGuest();
        return;
      }
      remaining--;
    };
    tick();
    accountTimer = setInterval(tick, 1000);
  }

  function showAccountPrompt() {
    $("account-title").textContent = UI[lang].accountTitle;
    $("account-prompt").textContent = UI[lang].accountPrompt;
    $("account-code-label").textContent = UI[lang].accountCodeLabel;
    $("account-submit").textContent = UI[lang].accountSubmit;
    $("account-guest").textContent = UI[lang].accountGuest;
    $("account-code-input").value = "";
    $("account-error").textContent = "";
    show("account");
    startAccountTimer();
    $("account-code-input").focus();
  }

  function submitAccountCode(event) {
    event.preventDefault();
    const code = $("account-code-input").value.trim();
    if (!code) {
      $("account-error").textContent = UI[lang].accountRequired;
      $("account-code-input").focus();
      return;
    }
    if (code.length > 128) {
      $("account-error").textContent = UI[lang].accountTooLong;
      $("account-code-input").focus();
      return;
    }
    stopAccountTimer();
    accountCode = code;
    sessionStorage.removeItem("quizVisitor");
    showCategories();
  }

  // Language button: switch texts and reading direction, then ask for an account code.
  function setLang(code) {
    lang = code;
    document.documentElement.lang = code;
    document.documentElement.dir = code === "ar" ? "rtl" : "ltr"; // Arabic reads right to left
    showAccountPrompt();
  }

  function showCategories() {
    $("cats-title").textContent = UI[lang].pick;
    $("leaderboard-open").textContent = UI[lang].checkLeaderboard;
    $("leaderboard-title").textContent = UI[lang].leaderboard;
    $("leaderboard-back").textContent = UI[lang].leaderboardBack;
    $("leaderboard-retry").textContent = UI[lang].leaderboardRetry;
    $("leaderboard-place-heading").textContent = UI[lang].place;
    $("leaderboard-user-heading").textContent = UI[lang].visitor;
    $("leaderboard-points-heading").textContent = UI[lang].leaderboardPoints;
    $("end-label").textContent = UI[lang].score;
    $("again").textContent = UI[lang].again;
    $("again").disabled = false;
    $("before-label").textContent = UI[lang].before;
    $("now-label").textContent = UI[lang].now;
    $("check-points").textContent = UI[lang].checkPoints;
    $("points-title").textContent = UI[lang].pointsTitle;
    $("history-title").textContent = UI[lang].historyTitle;
    $("points-back").textContent = UI[lang].pointsBack;
    $("rating-title").textContent = UI[lang].ratingTitle;
    $("rating-submit").textContent = UI[lang].ratingSubmit;
    $("rating-skip").textContent = UI[lang].ratingSkip;
    $("rating-close").setAttribute("aria-label", UI[lang].ratingSkip);
    renderRatingOptions();
    const list = $("cat-list");
    list.innerHTML = "";
    CATEGORIES.forEach((c, n) => {
      const b = document.createElement("button");
      b.className = "choice c" + n;
      b.textContent = tr(c.name);
      b.onclick = () => start(c.key);
      list.appendChild(b);
    });
    $("leaderboard-open").onclick = () => showLeaderboard();
    show("cats");
  }

  function showLeaderboard() {
    leaderboardRequest++;
    $("leaderboard-title").textContent = UI[lang].leaderboard;
    $("leaderboard-back").textContent = UI[lang].leaderboardBack;
    renderLeaderboardControls();
    show("leaderboard");
  }

  function renderLeaderboardControls() {
    const categories = $("leaderboard-categories");
    categories.innerHTML = "";
    CATEGORIES.forEach((item) => {
      const button = document.createElement("button");
      button.className = "leaderboard-tab";
      button.textContent = tr(item.name);
      button.setAttribute("aria-pressed", String(item.key === leaderboardCategory));
      button.onclick = () => {
        if (leaderboardCategory === item.key) return;
        leaderboardCategory = item.key;
        renderLeaderboardControls();
      };
      categories.appendChild(button);
    });

    const periods = $("leaderboard-periods");
    periods.innerHTML = "";
    ["daily", "monthly"].forEach((period) => {
      const button = document.createElement("button");
      button.className = "leaderboard-tab";
      button.textContent = UI[lang][period];
      button.setAttribute("aria-pressed", String(period === leaderboardPeriod));
      button.onclick = () => {
        if (leaderboardPeriod === period) return;
        leaderboardPeriod = period;
        renderLeaderboardControls();
      };
      periods.appendChild(button);
    });
    loadLeaderboard();
  }

  async function loadLeaderboard() {
    const requestId = ++leaderboardRequest;
    const status = $("leaderboard-status");
    const results = $("leaderboard-results");
    const list = $("leaderboard-list");
    const podium = $("leaderboard-podium");
    const retry = $("leaderboard-retry");
    status.textContent = UI[lang].leaderboardLoading;
    results.hidden = true;
    retry.hidden = true;
    list.innerHTML = "";
    podium.innerHTML = "";
    try {
      const query = new URLSearchParams({
        category: leaderboardCategory,
        period: leaderboardPeriod,
      });
      const response = await fetch("/api/leaderboard?" + query);
      if (!response.ok) throw new Error("Could not load leaderboard.");
      const result = await response.json();
      if (requestId !== leaderboardRequest) return;
      results.hidden = result.entries.length === 0;
      status.textContent = result.entries.length
        ? ""
        : UI[lang].leaderboardEmpty;
      const medals = {
        1: { symbol: "🥇", label: "Gold medal" },
        2: { symbol: "🥈", label: "Silver medal" },
        3: { symbol: "🥉", label: "Bronze medal" },
      };
      [2, 1, 3].forEach((rank) => {
        const entry = result.entries[rank - 1];
        const place = document.createElement("div");
        place.className = "podium-place podium-place-" + rank;
        if (!entry) {
          place.classList.add("podium-place-empty");
          podium.appendChild(place);
          return;
        }
        const trophy = document.createElement("span");
        trophy.className = "podium-trophy";
        trophy.textContent = medals[rank].symbol;
        trophy.setAttribute("aria-label", medals[rank].label);
        const name = document.createElement("span");
        name.className = "podium-user";
        name.textContent = entry.player;
        const block = document.createElement("div");
        block.className = "podium-block";
        block.textContent = rank;
        place.append(trophy, name, block);
        podium.appendChild(place);
      });
      result.entries.forEach((entry, index) => {
        const row = document.createElement("li");
        row.className = "leaderboard-row";
        if (entry.player === sessionStorage.getItem("quizVisitor")) {
          row.classList.add("leaderboard-current-user");
          row.setAttribute("aria-current", "true");
        }
        const place = document.createElement("span");
        place.className = "leaderboard-place";
        const rankNumber = document.createElement("span");
        rankNumber.textContent = index + 1;
        place.appendChild(rankNumber);
        if (index < 3) {
          place.classList.add("leaderboard-rank-" + (index + 1));
          const trophy = document.createElement("span");
          trophy.className = "leaderboard-trophy";
          trophy.textContent = medals[index + 1].symbol;
          trophy.setAttribute("aria-label", medals[index + 1].label);
          place.prepend(trophy);
        }
        const player = document.createElement("span");
        player.className = "leaderboard-user";
        player.textContent = entry.player;
        const points = document.createElement("strong");
        points.className = "leaderboard-score";
        points.textContent = entry.score;
        row.append(place, player, points);
        list.appendChild(row);
        if (row.classList.contains("leaderboard-current-user")) {
          row.scrollIntoView({ block: "center", behavior: "smooth" });
        }
      });
    } catch (error) {
      if (requestId !== leaderboardRequest) return;
      results.hidden = true;
      status.textContent = UI[lang].leaderboardError;
      retry.hidden = false;
    }
  }

  function start(key) {
    clearLeds(); // a new visitor starts with all LEDs off
    category = key;
    questions = pickQuestions(key);
    i = 0;
    score = 0;
    correctQuestionIds = [];
    gameStartedAt = Date.now();
    render();
    show("play");
  }

  function setProgress(n) {
    $("fill").style.transform = "scaleX(" + n / questions.length + ")";
  }

  // An <img> for one picture path (relative to the output folder).
  function picture(path) {
    const img = new Image();
    img.src = OUTPUT_DIR + path;
    img.alt = "";
    img.onerror = () => img.remove();
    return img;
  }

  function render() {
    const q = questions[i];
    // Questions 4, 7, 10... start a new group of 3: switch the LEDs off first.
    if (i > 0 && i % LED_COUNT === 0) clearLeds();
    $("count").textContent = i + 1 + " / " + questions.length;
    setProgress(i);
    $("q-text").textContent = questionText(q);
    // 2 pictures: the pictures ARE the answer buttons, so the big picture area is hidden.
    const twoPictures = imagesOf(q).length === 2;
    const pic = $("pic");
    pic.innerHTML = "";
    pic.hidden = twoPictures;
    if (!twoPictures) pic.appendChild(picture(imagesOf(q)[0]));
    const box = $("answers");
    box.className = twoPictures ? "answers pictures" : "answers";
    box.innerHTML = "";
    // Shuffle whole options (not just texts), so English and Arabic stay together.
    // Works for 4 options and for 2.
    shuffle(optionsOf(q)).forEach((option) => {
      const b = document.createElement("button");
      b.className = "ans";
      if (twoPictures)
        b.appendChild(picture("images/" + option.en)); // option = file name
      else b.textContent = display(tr(option));
      b.dataset.answer = option.en; // the exact English text, used to check the answer
      b.onclick = () => pick(b);
      box.appendChild(b);
    });
  }

  // Ask the Pi's server (game/app.py) to switch the LEDs.
  // Without the server (index.html opened by double-click) the request fails
  // quietly and the game simply carries on.
  const LED_COUNT = 3;
  const ledRequest = (path) =>
    fetch("/api/led/" + path, { method: "POST" }).catch(() => {});
  // Answer 1 -> LED 0, answer 2 -> LED 1, answer 3 -> LED 2, answer 4 -> LED 0 again...
  const setLed = (questionIndex, result) =>
    ledRequest((questionIndex % LED_COUNT) + "/" + result);
  const clearLeds = () => ledRequest("clear");

  function pick(btn) {
    const q = questions[i],
      box = $("answers");
    box.classList.add("locked");
    const correct = btn.dataset.answer === answerOf(q);
    if (correct) {
      score++;
      correctQuestionIds.push(q.id);
    }
    else btn.classList.add("wrong");
    setLed(i, correct ? "correct" : "wrong");
    // Always highlight the correct answer, so a wrong guess still shows it.
    [...box.children]
      .find((b) => b.dataset.answer === answerOf(q))
      .classList.add("correct");
    showArtworkInfo(q, correct);
    setProgress(i + 1);
    setTimeout(() => {
      if (++i < questions.length) render();
      else finish();
    }, FEEDBACK_TIME);
  }

  // After answering: title and date on the picture. Right: only the correct artwork.
  // Wrong: both. artworks[0] is always the correct one (see export_year_questions.py).
  function showArtworkInfo(q, correct) {
    if (!q.artworks) return; // Origin questions have no artwork info
    const shown = correct ? [q.artworks[0]] : q.artworks;
    shown.forEach((art) => {
      const caption = document.createElement("div");
      caption.className = "caption";
      // tr() picks the visitor's language and falls back to English if the Arabic is empty
      caption.textContent = tr(art.title) + ", " + tr(art.date);
      // 2 pictures: the caption goes on the button with this artwork; 1 picture: on the big picture.
      const holder =
        imagesOf(q).length === 2
          ? [...$("answers").children].find(
              (b) => b.dataset.answer === art.file,
            )
          : $("pic");
      holder.appendChild(caption);
    });
  }

  function finish() {
    clearLeds(); // the score screen has no LEDs on
    const t = questions.length;
    $("score").innerHTML = score + "<small>/" + t + "</small>";
    $("verdict").textContent =
      UI[lang].v[score === t ? 2 : score >= t / 2 ? 1 : 0];
    show("end");
    if (accountCode) {
      saveAccountScore();
    } else {
      setSaveStatus("guest", UI[lang].guestTitle, UI[lang].guestMessage);
      showRating(false);
    }
  }

  const RATING_FACES = [
    '<svg viewBox="0 0 56 56" aria-hidden="true" focusable="false"><circle cx="28" cy="28" r="22" fill="#ef4148" stroke="#222" stroke-width="4"/><circle cx="20" cy="23" r="2.5" fill="#222"/><circle cx="36" cy="23" r="2.5" fill="#222"/><path d="M17 39 Q28 28 39 39" fill="none" stroke="#222" stroke-width="3.5" stroke-linecap="round"/></svg>',
    '<svg viewBox="0 0 56 56" aria-hidden="true" focusable="false"><circle cx="28" cy="28" r="22" fill="#efb08c" stroke="#222" stroke-width="4"/><circle cx="20" cy="23" r="2.5" fill="#222"/><circle cx="36" cy="23" r="2.5" fill="#222"/><path d="M19 38 Q28 33 37 38" fill="none" stroke="#222" stroke-width="3.5" stroke-linecap="round"/></svg>',
    '<svg viewBox="0 0 56 56" aria-hidden="true" focusable="false"><circle cx="28" cy="28" r="22" fill="#f8efcf" stroke="#222" stroke-width="4"/><circle cx="20" cy="23" r="2.5" fill="#222"/><circle cx="36" cy="23" r="2.5" fill="#222"/><path d="M19 36 H37" fill="none" stroke="#222" stroke-width="3.5" stroke-linecap="round"/></svg>',
    '<svg viewBox="0 0 56 56" aria-hidden="true" focusable="false"><circle cx="28" cy="28" r="22" fill="#f8d45b" stroke="#222" stroke-width="4"/><circle cx="20" cy="23" r="2.5" fill="#222"/><circle cx="36" cy="23" r="2.5" fill="#222"/><path d="M18 33 Q28 43 38 33" fill="none" stroke="#222" stroke-width="3.5" stroke-linecap="round"/></svg>',
    '<svg viewBox="0 0 56 56" aria-hidden="true" focusable="false"><circle cx="28" cy="28" r="22" fill="#76c87d" stroke="#222" stroke-width="4"/><circle cx="20" cy="23" r="2.5" fill="#222"/><circle cx="36" cy="23" r="2.5" fill="#222"/><path d="M17 32 Q28 46 39 32 Z" fill="#222"/></svg>',
  ];

  function renderRatingOptions() {
    const options = $("rating-options");
    options.innerHTML = "";
    UI[lang].ratingLabels.forEach((label, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "rating-option";
      button.innerHTML = RATING_FACES[index];
      button.setAttribute("aria-label", label);
      button.setAttribute("aria-pressed", "false");
      button.onclick = () => {
        ratingScore = index + 1;
        [...options.children].forEach((option, optionIndex) =>
          option.setAttribute("aria-pressed", String(optionIndex === index)),
        );
        $("rating-submit").disabled = false;
        $("rating-status").textContent = "";
      };
      options.appendChild(button);
    });
  }

  function showRating(scoreSaved) {
    ratingScore = null;
    $("rating-status").textContent = "";
    $("rating-submit").disabled = true;
    $("rating-submit").textContent = UI[lang].ratingSubmit;
    $("rating-modal").hidden = false;
    renderRatingOptions();
    $("rating-options").firstElementChild.focus();
    $("rating-modal").dataset.scoreSaved = String(scoreSaved);
  }

  function closeRating() {
    $("rating-modal").hidden = true;
  }

  async function submitRating() {
    if (ratingScore === null) return;
    const submit = $("rating-submit");
    submit.disabled = true;
    $("rating-status").textContent = "";
    try {
      const reply = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category,
          score,
          rating: ratingScore,
          language: lang,
          score_saved: $("rating-modal").dataset.scoreSaved === "true",
          duration_seconds: Math.max(0, Math.floor((Date.now() - gameStartedAt) / 1000)),
        }),
      });
      if (!reply.ok) throw new Error("Could not save rating.");
      closeRating();
    } catch (error) {
      $("rating-status").textContent = UI[lang].ratingError;
      submit.disabled = false;
    }
  }

  function showPoints(result) {
    const balance = result.points_balance;
    $("points-total").textContent = balance;
    $("points-target").textContent =
      balance >= 40 ? UI[lang].rewardReady : UI[lang].pointsNeeded(balance);
    $("points-fill").style.transform =
      "scaleX(" + Math.min(balance / 40, 1) + ")";
    document
      .querySelector(".points-track")
      .setAttribute("aria-valuenow", Math.min(balance, 40));
    const history = $("points-history");
    history.innerHTML = "";
    result.points_history.forEach((entry) => {
      const item = document.createElement("li");
      const categoryName = CATEGORIES.find(
        (item) => item.key === entry.category,
      )?.name;
      const detail = document.createElement("span");
      detail.textContent =
        (entry.kind === "redeemed"
          ? UI[lang].redeemedEntry
          : UI[lang].earnedEntry) +
        " · " +
        (categoryName ? tr(categoryName) : entry.category) +
        " · " +
        new Intl.DateTimeFormat(lang, { dateStyle: "medium" }).format(
          new Date(entry.created_at),
        );
      const points = document.createElement("strong");
      points.textContent = (entry.points > 0 ? "+" : "") + entry.points;
      item.append(detail, points);
      history.appendChild(item);
    });
    show("points");
  }

  function setSaveStatus(state, title, message) {
    $("save-panel").dataset.state = state;
    $("save-title").textContent = title;
    $("save-message").textContent = message;
    $("score-compare").hidden = true;
    $("points-earned").hidden = true;
    $("check-points").hidden = true;
  }

  async function saveAccountScore() {
    $("again").disabled = true;
    setSaveStatus("waiting", UI[lang].savingTitle, UI[lang].savingMessage);
    try {
      const reply = await fetch("/api/account/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          account_code: accountCode,
          category,
          score,
          correct_question_ids: correctQuestionIds,
        }),
      });
      const result = await reply.json();
      if (!reply.ok) throw new Error(result.error || UI[lang].saveFailed);
      if (!result.saved) throw new Error(UI[lang].saveFailed);

      lastPointsResult = result;
      sessionStorage.setItem("quizVisitor", result.visitor);
      setSaveStatus("saved", UI[lang].savedTitle, UI[lang].saved);
      if (result.quizzes_today === 1) {
        $("points-earned").textContent = UI[lang].pointsPending;
      } else if (result.quizzes_today === 3) {
        $("points-earned").textContent = UI[lang].thirdQuizPoints(
          result.points_earned,
        );
      } else if (result.quizzes_today >= 4) {
        $("points-earned").textContent = UI[lang].dailyLimit;
      } else {
        $("points-earned").textContent = UI[lang].earned(
          result.points_earned,
        );
      }
      $("points-earned").textContent +=
        "\n" +
        UI[lang].dailyProgress(
          result.leaderboard_score,
          result.leaderboard_points_earned,
        );
      $("points-earned").hidden = false;
      $("check-points").hidden = false;
      if (result.quizzes_today > 1) {
        $("before-score").textContent = result.first_score + "/" + questions.length;
        $("now-score").textContent = score + "/" + questions.length;
        $("score-compare").hidden = false;
      }
      showRating(true);
    } catch (error) {
      setSaveStatus(
        "error",
        UI[lang].saveFailed,
        error instanceof Error ? error.message : UI[lang].saveFailed,
      );
      showRating(false);
    } finally {
      $("again").disabled = false;
    }
  }

  $("account-form").addEventListener("submit", submitAccountCode);
  $("account-guest").onclick = continueAsGuest;
  $("rating-submit").onclick = submitRating;
  $("rating-skip").onclick = closeRating;
  $("rating-close").onclick = closeRating;
  $("check-points").onclick = () => showPoints(lastPointsResult);
  $("points-back").onclick = () => show("end");
  $("leaderboard-back").onclick = () => show("cats");
  $("leaderboard-retry").onclick = () => loadLeaderboard();

  document
    .querySelectorAll("[data-lang]")
    .forEach((b) => (b.onclick = () => setLang(b.dataset.lang)));
  // Play again: return to language selection and ask for an account code again.
  $("again").onclick = () => {
    accountCode = null;
    stopAccountTimer();
    document.documentElement.lang = "en";
    document.documentElement.dir = "ltr";
    show("lang");
  };
})();
