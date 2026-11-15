(() => {
  const $ = (id) => document.getElementById(id);
  const stage = $("stage");

  const OUTPUT_DIR = "../../output/"; // question images live in output/images/
  const PER_GAME = 6; // questions per playthrough (fewer if the bank is smaller)
  const DAILY_QUESTION_COUNT = PER_GAME * 2;
  const ORIGIN_PER_TYPE = 3; // Origin: 3 continent + 3 country questions
  const FEEDBACK_TIME = 3000; // milliseconds to show the result before the next question
  const HOME_ARTWORK_FILE = "2007.1.1639a.2000x2000.jpg";

  // Category buttons: key in QUIZ_DATA.categories -> label on screen, per language.
  const CATEGORIES = [
    { key: "year", name: { en: "Year of Creation", ar: "سنة الإنشاء" } },
    { key: "origin", name: { en: "Geographic Origin", ar: "الأصل الجغرافي" } },
  ];
  const UI = {
    en: {
      languageLabel: "Language",
      play: "Play",
      homeArtworkAlt: "Artwork from the museum collection",
      pick: "Choose a category",
      exit: "Exit",
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
      dailyAverage: (average) =>
        `Average score by visitors today is: ${average}.`,
      averageChallenge: "Can you beat the average?",
      averageEmpty: "No scores yet",
      averageError: "Today's average couldn't be loaded.",
      accountTitle: "Save your scores and points",
      accountPrompt: "Choose how you would like to continue.",
      accountCodePrompt:
        "Enter your account code or create a new account.",
      accountSignIn: "Sign In / Sign Up",
      accountBack: "Back",
      accountCodeLabel: "Account code",
      accountSubmit: "Use code",
      accountCreateOpen: "Create a new account",
      accountNameLabel: "Display name",
      accountCreateSubmit: "Create account",
      accountCreateBack: "Back to account code",
      accountCreatedMessage: "Your account code is:",
      accountCreatedReminder:
        "Write it down. You will need this code to use your account again.",
      accountCreatedContinue: "Continue",
      accountNameRequired: "Enter a display name.",
      accountNameTooLong: "The display name must be 40 characters or fewer.",
      accountNameInvalid: "Use a name without line breaks or control characters.",
      accountServiceError:
        "Account service error. Ask staff to restart the kiosk.",
      accountCodeNotFound: "We couldn't find that account code.",
      accountRequestError: "We couldn't connect to the account service. Try again.",
      accountGuest: "Continue as Guest",
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
      guestMessage: "Score not saved.",
      saveFailed: "We couldn't save your score. Please ask museum staff for help.",
      before: "Before",
      now: "Now",
      earned: (points) => `You earned ${points} points.`,
      firstQuizPending:
        "Quiz saved. Your points will be added after your second quiz in this category today.",
      thirdQuizPending:
        "Quiz saved. Your points will be added after your fourth quiz in this category today.",
      dailyLimit: "No more points will be saved in this category until tomorrow.",
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
      languageLabel: "اللغة",
      play: "ابدأ",
      homeArtworkAlt: "عمل فني من مجموعة المتحف",
      pick: "اختر فئة",
      exit: "خروج",
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
      dailyAverage: (average) =>
        `متوسط نتيجة الزوار اليوم: ${average}.`,
      averageChallenge: "هل يمكنك تجاوز المتوسط؟",
      averageEmpty: "لا توجد نتائج بعد",
      averageError: "تعذر تحميل متوسط اليوم.",
      accountTitle: "احفظ نتائجك ونقاطك",
      accountPrompt: "اختر طريقة المتابعة.",
      accountCodePrompt: "أدخل رمز حسابك أو أنشئ حسابًا جديدًا.",
      accountSignIn: "تسجيل الدخول / إنشاء حساب",
      accountBack: "رجوع",
      accountCodeLabel: "رمز الحساب",
      accountSubmit: "استخدم الرمز",
      accountCreateOpen: "إنشاء حساب جديد",
      accountNameLabel: "الاسم المعروض",
      accountCreateSubmit: "إنشاء حساب",
      accountCreateBack: "العودة إلى رمز الحساب",
      accountCreatedMessage: "رمز حسابك هو:",
      accountCreatedReminder:
        "اكتب الرمز واحتفظ به. ستحتاج إليه لاستخدام حسابك مرة أخرى.",
      accountCreatedContinue: "متابعة",
      accountNameRequired: "أدخل اسمًا معروضًا.",
      accountNameTooLong: "يجب ألا يتجاوز الاسم المعروض 40 حرفًا.",
      accountNameInvalid: "استخدم اسمًا بلا أسطر جديدة أو محارف تحكم.",
      accountServiceError:
        "حدث خطأ في خدمة الحسابات. اطلب من الموظفين إعادة تشغيل الجهاز.",
      accountCodeNotFound: "لم نعثر على حساب بهذا الرمز.",
      accountRequestError: "تعذر الاتصال بخدمة الحسابات. حاول مرة أخرى.",
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
      guestMessage: "لم يتم حفظ النتيجة.",
      saveFailed: "تعذر حفظ نتيجتك. يُرجى طلب المساعدة من موظفي المتحف.",
      before: "قبل",
      now: "الآن",
      earned: (points) => `لقد حصلت على ${points} نقاط.`,
      firstQuizPending:
        "تم حفظ الاختبار. ستُضاف نقاطك بعد إكمال الاختبار الثاني في هذه الفئة اليوم.",
      thirdQuizPending:
        "تم حفظ الاختبار. ستُضاف نقاطك بعد إكمال الاختبار الرابع في هذه الفئة اليوم.",
      dailyLimit: "لن تُحفظ نقاط أخرى في هذه الفئة حتى الغد.",
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

  let lang = sessionStorage.getItem("quizLanguage") === "ar" ? "ar" : "en",
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
    leaderboardRequest = 0,
    idleTimer = null,
    dailyAverage = null,
    dailyAverageError = false,
    questionAnswered = false,
    selectedAnswer = null,
    accountErrorKey = null,
    accountSecondsRemaining = 0,
    saveErrorText = null;

  const ACCOUNT_CODE_TIMEOUT_SECONDS = 30;
  const IDLE_TIMEOUT_MS = 120000;

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
    resetIdleTimer();
  }

  function resetIdleTimer() {
    if (idleTimer !== null) clearTimeout(idleTimer);
    idleTimer = null;
    if (stage.dataset.screen === "home") return;
    idleTimer = setTimeout(exitToHome, IDLE_TIMEOUT_MS);
  }

  function exitToHome() {
    stopAccountTimer();
    accountCode = null;
    sessionStorage.removeItem("quizVisitor");
    $("rating-modal").hidden = true;
    clearLeds();
    showHome();
  }

  function updateLanguageControl() {
    $("language-control").setAttribute("aria-label", UI[lang].languageLabel);
    document.querySelectorAll("[data-lang]").forEach((button) => {
      button.textContent = button.dataset.lang === "en" ? "English" : "عربي";
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.lang === lang),
      );
    });
  }

  function applyDocumentLanguage() {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    updateLanguageControl();
  }

  function updateHomeLanguage() {
    $("home-play").textContent = UI[lang].play;
    $("home-art").alt = UI[lang].homeArtworkAlt;
  }

  function showHome() {
    updateHomeLanguage();
    $("home-art").src =
      OUTPUT_DIR + "images/" + encodeURIComponent(HOME_ARTWORK_FILE);
    show("home");
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
    accountSecondsRemaining = ACCOUNT_CODE_TIMEOUT_SECONDS;
    const tick = () => {
      $("account-countdown").textContent =
        UI[lang].accountCountdown(accountSecondsRemaining);
      if (accountSecondsRemaining === 0) {
        continueAsGuest();
        return;
      }
      accountSecondsRemaining--;
    };
    tick();
    accountTimer = setInterval(tick, 1000);
  }

  const ACCOUNT_ERROR_KEYS = [
    "accountRequired",
    "accountTooLong",
    "accountCodeNotFound",
    "accountRequestError",
    "accountNameRequired",
    "accountNameTooLong",
    "accountNameInvalid",
    "accountServiceError",
  ];

  function clearAccountError() {
    accountErrorKey = null;
    $("account-error").textContent = "";
    $("account-error").hidden = true;
  }

  function setAccountError(key) {
    accountErrorKey = key;
    $("account-error").textContent = UI[lang][key];
    $("account-error").hidden = false;
  }

  function setAccountErrorFrom(error, fallbackKey) {
    const key = ACCOUNT_ERROR_KEYS.find(
      (candidate) =>
        error instanceof Error && error.message === UI[lang][candidate],
    );
    setAccountError(key || fallbackKey);
  }

  function updateAccountLanguage() {
    $("account-title").textContent = UI[lang].accountTitle;
    $("account-prompt").textContent = $("account-choice").hidden
      ? UI[lang].accountCodePrompt
      : UI[lang].accountPrompt;
    $("account-signin").textContent = UI[lang].accountSignIn;
    $("account-guest").textContent = UI[lang].accountGuest;
    $("account-back").textContent = UI[lang].accountBack;
    $("account-code-label").textContent = UI[lang].accountCodeLabel;
    $("account-submit").textContent = UI[lang].accountSubmit;
    $("account-create-open").textContent = UI[lang].accountCreateOpen;
    $("account-name-label").textContent = UI[lang].accountNameLabel;
    $("account-create-submit").textContent = UI[lang].accountCreateSubmit;
    $("account-create-back").textContent = UI[lang].accountCreateBack;
    $("account-created-message").textContent = UI[lang].accountCreatedMessage;
    $("account-created-reminder").textContent =
      UI[lang].accountCreatedReminder;
    $("account-created-continue").textContent =
      UI[lang].accountCreatedContinue;
    if (accountErrorKey) {
      $("account-error").textContent = UI[lang][accountErrorKey];
    }
    if (accountTimer !== null && !$("account-countdown").hidden) {
      $("account-countdown").textContent =
        UI[lang].accountCountdown(accountSecondsRemaining);
    }
  }

  function showAccountPrompt() {
    sessionStorage.removeItem("quizVisitor");
    $("account-code-input").value = "";
    $("account-name-input").value = "";
    clearAccountError();
    $("account-choice").hidden = false;
    $("account-form").hidden = true;
    $("account-create-form").hidden = true;
    $("account-create-open").hidden = true;
    $("account-created").hidden = true;
    $("account-countdown").hidden = false;
    $("account-back").hidden = true;
    updateAccountLanguage();
    show("account");
    startAccountTimer();
    $("account-signin").focus();
  }

  function showAccountOptions() {
    stopAccountTimer();
    $("account-prompt").textContent = UI[lang].accountCodePrompt;
    $("account-choice").hidden = true;
    $("account-form").hidden = false;
    $("account-create-open").hidden = false;
    $("account-create-form").hidden = true;
    $("account-created").hidden = true;
    clearAccountError();
    $("account-countdown").hidden = true;
    $("account-back").hidden = false;
    $("account-code-input").focus();
  }

  function returnToAccountChoice() {
    $("account-choice").hidden = false;
    $("account-form").hidden = true;
    $("account-create-open").hidden = true;
    $("account-create-form").hidden = true;
    $("account-created").hidden = true;
    clearAccountError();
    $("account-countdown").hidden = false;
    $("account-back").hidden = true;
    $("account-prompt").textContent = UI[lang].accountPrompt;
    startAccountTimer();
    $("account-signin").focus();
  }

  function showCreateAccountForm() {
    stopAccountTimer();
    clearAccountError();
    $("account-form").hidden = true;
    $("account-create-open").hidden = true;
    $("account-create-form").hidden = false;
    $("account-back").hidden = true;
    $("account-name-input").focus();
  }

  function returnToAccountCode() {
    $("account-create-form").hidden = true;
    $("account-form").hidden = false;
    $("account-create-open").hidden = false;
    $("account-back").hidden = false;
    $("account-name-input").value = "";
    clearAccountError();
    $("account-code-input").focus();
  }

  async function submitAccountCode(event) {
    event.preventDefault();
    const code = $("account-code-input").value.trim();
    if (!code) {
      setAccountError("accountRequired");
      $("account-code-input").focus();
      return;
    }
    if (code.length > 128) {
      setAccountError("accountTooLong");
      $("account-code-input").focus();
      return;
    }
    stopAccountTimer();
    clearAccountError();
    $("account-submit").disabled = true;
    $("account-create-open").disabled = true;
    $("account-guest").disabled = true;
    try {
      const response = await fetch("/api/account/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account_code: code }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(
          response.status === 404
            ? UI[lang].accountCodeNotFound
            : UI[lang].accountRequestError,
        );
      }
      accountCode = code;
      sessionStorage.setItem("quizVisitor", result.visitor);
      showCategories();
    } catch (error) {
      setAccountErrorFrom(error, "accountRequestError");
    } finally {
      $("account-submit").disabled = false;
      $("account-create-open").disabled = false;
      $("account-guest").disabled = false;
    }
  }

  async function submitNewAccount(event) {
    event.preventDefault();
    const displayName = $("account-name-input").value.trim();
    if (!displayName) {
      setAccountError("accountNameRequired");
      $("account-name-input").focus();
      return;
    }
    if (displayName.length > 40) {
      setAccountError("accountNameTooLong");
      $("account-name-input").focus();
      return;
    }

    clearAccountError();
    $("account-create-submit").disabled = true;
    $("account-create-back").disabled = true;
    $("account-guest").disabled = true;
    stopAccountTimer();
    try {
      const response = await fetch("/api/account/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ display_name: displayName }),
      });
      const contentType = response.headers.get("content-type") || "";
      if (!contentType.includes("application/json")) {
        throw new Error(UI[lang].accountServiceError);
      }
      let result;
      try {
        result = await response.json();
      } catch (error) {
        if (error instanceof SyntaxError) {
          throw new Error(UI[lang].accountServiceError);
        }
        throw error;
      }
      if (!result || typeof result !== "object") {
        throw new Error(UI[lang].accountServiceError);
      }
      if (!response.ok) {
        const reason = typeof result.error === "string" ? result.error : "";
        if (/control characters/i.test(reason)) {
          throw new Error(UI[lang].accountNameInvalid);
        }
        if (/empty|required/i.test(reason)) {
          throw new Error(UI[lang].accountNameRequired);
        }
        if (/40 characters/i.test(reason)) {
          throw new Error(UI[lang].accountNameTooLong);
        }
        throw new Error(
          response.status === 400
            ? UI[lang].accountNameInvalid
            : UI[lang].accountServiceError,
        );
      }
      if (!/^[A-Z0-9]{6}$/.test(result.account_code || "")) {
        throw new Error(UI[lang].accountServiceError);
      }
      accountCode = result.account_code;
      sessionStorage.setItem("quizVisitor", result.visitor);
      $("account-created-code").textContent = result.account_code;
      $("account-form").hidden = true;
      $("account-create-form").hidden = true;
      $("account-create-open").hidden = true;
      $("account-created").hidden = false;
      clearAccountError();
      $("account-countdown").hidden = true;
      $("account-guest").hidden = true;
      $("account-back").hidden = true;
      $("account-created-continue").focus();
    } catch (error) {
      setAccountErrorFrom(error, "accountServiceError");
    } finally {
      $("account-create-submit").disabled = false;
      $("account-create-back").disabled = false;
      $("account-guest").disabled = false;
    }
  }

  // Language buttons update the visible screen without changing the visitor's place.
  function setLang(code) {
    if (code !== "en" && code !== "ar") return;
    if (lang === code) return;
    lang = code;
    sessionStorage.setItem("quizLanguage", lang);
    applyDocumentLanguage();

    switch (stage.dataset.screen) {
      case "home":
        updateHomeLanguage();
        break;
      case "account":
        updateAccountLanguage();
        break;
      case "cats":
        showCategories();
        break;
      case "leaderboard":
        showLeaderboard();
        break;
      case "play":
        render(true);
        break;
      case "end":
        updateEndLanguage();
        break;
      case "points":
        showPoints(lastPointsResult);
        break;
    }
  }

  function showCategories() {
    $("cats-title").textContent = UI[lang].pick;
    $("category-exit").textContent = UI[lang].exit;
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
        1: { image: "assets/medals/gold.svg", label: "Gold medal" },
        2: { image: "assets/medals/silver.svg", label: "Silver medal" },
        3: { image: "assets/medals/bronze.svg", label: "Bronze medal" },
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
        const trophy = document.createElement("img");
        trophy.className = "podium-trophy";
        trophy.src = medals[rank].image;
        trophy.alt = medals[rank].label;
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
          const trophy = document.createElement("img");
          trophy.className = "leaderboard-trophy";
          trophy.src = medals[index + 1].image;
          trophy.alt = medals[index + 1].label;
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
    questionAnswered = false;
    selectedAnswer = null;
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

  function render(preserveLeds = false) {
    const q = questions[i];
    // Questions 4, 7, 10... start a new group of 3: switch the LEDs off first.
    if (!preserveLeds && i > 0 && i % LED_COUNT === 0) clearLeds();
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
    if (questionAnswered) {
      box.classList.add("locked");
      const correctAnswer = answerOf(q);
      const selectedButton = [...box.children].find(
        (button) => button.dataset.answer === selectedAnswer,
      );
      if (selectedAnswer !== correctAnswer) {
        selectedButton.classList.add("wrong");
      }
      [...box.children]
        .find((button) => button.dataset.answer === correctAnswer)
        .classList.add("correct");
      showArtworkInfo(q, selectedAnswer === correctAnswer);
      setProgress(i + 1);
    }
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
    if (questionAnswered) return;
    questionAnswered = true;
    selectedAnswer = btn.dataset.answer;
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
      if (++i < questions.length) {
        questionAnswered = false;
        selectedAnswer = null;
        render();
      } else {
        finish();
      }
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

  function renderDailyAverage(includeChallenge) {
    const formattedAverage =
      dailyAverage === null
        ? UI[lang].averageEmpty
        : new Intl.NumberFormat(lang, {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1,
          }).format(dailyAverage) +
          "/" +
          DAILY_QUESTION_COUNT;
    const lines = [
      dailyAverageError
        ? UI[lang].averageError
        : UI[lang].dailyAverage(formattedAverage),
    ];
    if (includeChallenge && !dailyAverageError && dailyAverage !== null) {
      lines.push(UI[lang].averageChallenge);
    }
    $("daily-average").textContent = lines.join("\n");
    $("daily-average").hidden = false;
  }

  async function loadDailyAverage() {
    try {
      const response = await fetch("/api/average/today");
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || UI[lang].averageError);
      }
      if (
        result.average_score !== null &&
        (typeof result.average_score !== "number" ||
          !Number.isFinite(result.average_score))
      ) {
        throw new Error(UI[lang].averageError);
      }
      dailyAverage = result.average_score;
      dailyAverageError = false;
    } catch (error) {
      console.error("Could not load today's average score.", error);
      dailyAverageError = true;
    }
    if ($("save-panel").dataset.state === "guest") {
      renderDailyAverage(false);
    }
  }

  function finish() {
    clearLeds(); // the score screen has no LEDs on
    const t = questions.length;
    $("score").innerHTML = score + "<small>/" + t + "</small>";
    $("verdict").textContent =
      UI[lang].v[score === t ? 2 : score >= t / 2 ? 1 : 0];
    dailyAverage = null;
    dailyAverageError = false;
    show("end");
    if (accountCode) {
      saveAccountScore();
    } else {
      setSaveStatus("guest", "", UI[lang].guestMessage);
      renderDailyAverage(false);
      loadDailyAverage();
      showRating(false);
    }
  }

  function updateSavedScoreDetails(result) {
    if (
      typeof result.average_score === "number" &&
      Number.isFinite(result.average_score)
    ) {
      dailyAverage = result.average_score;
      dailyAverageError = false;
    } else {
      dailyAverage = null;
      dailyAverageError = true;
      console.error("The saved score response omitted today's average.");
    }
    if (result.quizzes_today === 1) {
      $("points-earned").textContent = UI[lang].firstQuizPending;
    } else if (result.quizzes_today === 3) {
      $("points-earned").textContent = UI[lang].thirdQuizPending;
    } else if (result.quizzes_today >= 4) {
      $("points-earned").textContent = UI[lang].dailyLimit;
    } else {
      $("points-earned").textContent = UI[lang].earned(result.points_earned);
    }
    $("points-earned").hidden = false;
    renderDailyAverage(true);
    $("check-points").hidden = false;
    if (result.quizzes_today > 1) {
      $("before-score").textContent = result.first_score + "/" + questions.length;
      $("now-score").textContent = score + "/" + questions.length;
      $("score-compare").hidden = false;
    }
  }

  function updateEndLanguage() {
    $("end-label").textContent = UI[lang].score;
    $("again").textContent = UI[lang].again;
    $("before-label").textContent = UI[lang].before;
    $("now-label").textContent = UI[lang].now;
    $("check-points").textContent = UI[lang].checkPoints;
    $("rating-title").textContent = UI[lang].ratingTitle;
    $("rating-submit").textContent = UI[lang].ratingSubmit;
    $("rating-skip").textContent = UI[lang].ratingSkip;
    $("rating-close").setAttribute("aria-label", UI[lang].ratingSkip);
    $("score").innerHTML =
      score + "<small>/" + (questions ? questions.length : 0) + "</small>";
    $("verdict").textContent = UI[lang].v[
      score === questions.length ? 2 : score >= questions.length / 2 ? 1 : 0
    ];

    const saveState = $("save-panel").dataset.state;
    if (saveState === "waiting") {
      setSaveStatus("waiting", UI[lang].savingTitle, UI[lang].savingMessage);
    } else if (saveState === "saved") {
      setSaveStatus("saved", UI[lang].savedTitle, "");
      if (lastPointsResult) updateSavedScoreDetails(lastPointsResult);
    } else if (saveState === "guest") {
      setSaveStatus("guest", "", UI[lang].guestMessage);
      renderDailyAverage(false);
    } else if (saveState === "error") {
      setSaveStatus(
        "error",
        UI[lang].saveFailed,
        saveErrorText || UI[lang].saveFailed,
      );
    }

    const ratingHasError = Boolean($("rating-status").textContent);
    $("rating-status").textContent = ratingHasError ? UI[lang].ratingError : "";
    renderRatingOptions();
    $("rating-submit").disabled = ratingScore === null;
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
      button.setAttribute(
        "aria-pressed",
        String(ratingScore === index + 1),
      );
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
    $("save-message").hidden = state === "saved";
    $("score-compare").hidden = true;
    $("points-earned").hidden = true;
    $("daily-average").hidden = true;
    $("check-points").hidden = true;
  }

  async function saveAccountScore() {
    $("again").disabled = true;
    saveErrorText = null;
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
      setSaveStatus("saved", UI[lang].savedTitle, "");
      updateSavedScoreDetails(result);
      showRating(true);
    } catch (error) {
      saveErrorText =
        error instanceof Error ? error.message : UI[lang].saveFailed;
      setSaveStatus(
        "error",
        UI[lang].saveFailed,
        saveErrorText,
      );
      showRating(false);
    } finally {
      $("again").disabled = false;
    }
  }

  $("account-form").addEventListener("submit", submitAccountCode);
  $("account-signin").onclick = showAccountOptions;
  $("account-create-open").onclick = showCreateAccountForm;
  $("account-create-form").addEventListener("submit", submitNewAccount);
  $("account-create-back").onclick = returnToAccountCode;
  $("account-created-continue").onclick = showCategories;
  $("account-back").onclick = returnToAccountChoice;
  $("account-guest").onclick = continueAsGuest;
  $("category-exit").onclick = exitToHome;
  $("home-play").onclick = () => showAccountPrompt();
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
  document.addEventListener("pointerdown", resetIdleTimer);
  document.addEventListener("touchstart", resetIdleTimer);
  document.addEventListener("keydown", resetIdleTimer);
  document.addEventListener("input", resetIdleTimer);
  document.addEventListener("change", resetIdleTimer);
  applyDocumentLanguage();
  showHome();
  // Keep accounts signed in across games; guests return to the landing page.
  $("again").onclick = () => {
    stopAccountTimer();
    if (accountCode) {
      showCategories();
    } else {
      exitToHome();
    }
  };
})();
