(() => {
  const $ = (id) => document.getElementById(id);
  const stage = $("stage");

  const OUTPUT_DIR = "../../output/"; // question images live in output/images/
  const PER_GAME = 6; // questions per playthrough (fewer if the bank is smaller)
  const ORIGIN_PER_TYPE = 3; // Origin: 3 continent + 3 country questions

  // Category buttons: key in QUIZ_DATA.categories -> label on screen, per language.
  const CATEGORIES = [
    { key: "title", name: { en: "Artwork Title", ar: "عنوان العمل الفني" } },
    { key: "year", name: { en: "Year of Creation", ar: "سنة الإنشاء" } },
    { key: "origin", name: { en: "Geographic Origin", ar: "الأصل الجغرافي" } },
    { key: "medium", name: { en: "Medium", ar: "الخامة" } },
  ];
  const UI = {
    en: {
      pick: "Choose a category",
      score: "Your score",
      again: "Play again",
      v: ["Try again.", "Well played.", "Perfect score."],
      tapTitle: "Save your score",
      tap: "Tap your card on the reader",
      skip: "Skip",
      savedTitle: "Score saved!",
      saved: "Come back after the exhibition and tap again.",
      progressTitle: "Your progress",
      before: "Before",
      now: "Now",
      noCardTitle: "Not saved",
      noCard: "No card was tapped.",
    },
    ar: {
      pick: "اختر فئة",
      score: "نتيجتك",
      again: "العب مرة أخرى",
      v: ["حاول مرة أخرى.", "أحسنت.", "نتيجة كاملة."],
      tapTitle: "احفظ نتيجتك",
      tap: "ضع بطاقتك على القارئ",
      skip: "تخطي",
      savedTitle: "تم حفظ نتيجتك!",
      saved: "عد بعد زيارة المعرض وضع بطاقتك مرة أخرى.",
      progressTitle: "تقدّمك",
      before: "قبل",
      now: "الآن",
      noCardTitle: "لم تُحفظ",
      noCard: "لم يتم وضع بطاقة.",
    },
  };

  let lang = "en",
    category,
    questions,
    i,
    score,
    cardWait = 0; // number of the current card wait; a reply from an older one is ignored

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

  // The question sentence in the current language, with {continent} filled in.
  function questionText(q) {
    const texts = QUIZ_DATA.texts[lang] || QUIZ_DATA.texts.en;
    const sentence =
      texts[q.question_key] || QUIZ_DATA.texts.en[q.question_key];
    return sentence.replace("{continent}", q.continent ? tr(q.continent) : "");
  }

  // Language button: switch texts and reading direction, then show the categories.
  function setLang(code) {
    lang = code;
    document.documentElement.lang = code;
    document.documentElement.dir = code === "ar" ? "rtl" : "ltr"; // Arabic reads right to left
    showCategories();
  }

  function showCategories() {
    $("cats-title").textContent = UI[lang].pick;
    $("end-label").textContent = UI[lang].score;
    $("again").textContent = UI[lang].again;
    $("skip").textContent = UI[lang].skip;
    $("before-label").textContent = UI[lang].before;
    $("now-label").textContent = UI[lang].now;
    const list = $("cat-list");
    list.innerHTML = "";
    CATEGORIES.forEach((c, n) => {
      const b = document.createElement("button");
      b.className = "choice c" + n;
      b.textContent = tr(c.name);
      b.onclick = () => start(c.key);
      list.appendChild(b);
    });
    show("cats");
  }

  function start(key) {
    clearLeds(); // a new visitor starts with all LEDs off
    category = key;
    questions = pickQuestions(key);
    i = 0;
    score = 0;
    render();
    show("play");
  }

  function setProgress(n) {
    $("fill").style.transform = "scaleX(" + n / questions.length + ")";
  }

  function render() {
    const q = questions[i];
    // Questions 4, 7, 10... start a new group of 3: switch the LEDs off first.
    if (i > 0 && i % LED_COUNT === 0) clearLeds();
    $("count").textContent = i + 1 + " / " + questions.length;
    setProgress(i);
    $("q-text").textContent = questionText(q);
    const pic = $("pic"),
      img = new Image();
    img.src = OUTPUT_DIR + q.image;
    img.alt = "";
    img.onerror = () => img.remove();
    pic.innerHTML = "";
    pic.appendChild(img);
    const box = $("answers");
    box.className = "answers";
    box.innerHTML = "";
    // Shuffle the positions 0-3, so the English and Arabic option at each position stay together.
    shuffle([0, 1, 2, 3]).forEach((n) => {
      const b = document.createElement("button");
      b.className = "ans";
      b.textContent = display(
        tr({ en: q.options.en[n], ar: q.options.ar && q.options.ar[n] }),
      );
      b.dataset.answer = q.options.en[n]; // the exact English text, used to check the answer
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
    const correct = btn.dataset.answer === q.answer.en;
    if (correct) score++;
    else btn.classList.add("wrong");
    setLed(i, correct ? "correct" : "wrong");
    // Always highlight the correct answer, so a wrong guess still shows it.
    [...box.children]
      .find((b) => b.dataset.answer === q.answer.en)
      .classList.add("correct");
    setProgress(i + 1);
    setTimeout(() => {
      if (++i < questions.length) render();
      else finish();
    }, 1200);
  }

  function finish() {
    clearLeds(); // the score screen has no LEDs on
    const t = questions.length;
    $("score").innerHTML = score + "<small>/" + t + "</small>";
    $("verdict").textContent =
      UI[lang].v[score === t ? 2 : score >= t / 2 ? 1 : 0];
    show("end");
    waitForCard(t);
  }

  // Ask the Pi's server to wait (up to 20 s) for an RFID card and save the score under it.
  // The server only answers once a card is tapped or the time is up.
  // Switch the scan box to a state ("waiting", "saved" or "expired") with its title and text.
  // The CSS uses data-state for the colours and to hide the progress bar.
  function setScan(state, title, text) {
    $("scan").dataset.state = state;
    $("scan-title").textContent = title;
    $("scan-text").textContent = text;
    $("scan-compare").hidden = true;
    $("skip").hidden = state !== "waiting";
  }

  // Restart the 20 s progress bar: jump back to empty without animation, then fill slowly.
  function startScanTimer() {
    const fill = $("scan-fill");
    fill.classList.remove("scan-fill-run");
    fill.style.transform = "scaleX(0)";
    void fill.offsetWidth; // makes the browser apply the jump before the animation starts
    fill.classList.add("scan-fill-run");
    fill.style.transform = "scaleX(1)";
  }

  // Ask the Pi's server to wait (up to 20 s) for an RFID card and save the score under it.
  // The server only answers once a card is tapped or the time is up.
  function waitForCard(t) {
    const thisWait = ++cardWait;
    setScan("waiting", UI[lang].tapTitle, UI[lang].tap);
    startScanTimer();
    fetch("/api/card/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category: category, score: score }),
    })
      .then((reply) => reply.json())
      .then((result) => {
        if (thisWait !== cardWait) return; // visitor pressed Skip or Play again meanwhile
        if (!result.saved) setScan("expired", UI[lang].noCardTitle, UI[lang].noCard);
        else if (result.attempt === 1) setScan("saved", UI[lang].savedTitle, UI[lang].saved);
        else {
          setScan("saved", UI[lang].progressTitle, "");
          $("before-score").textContent = result.first_score + "/" + t;
          $("now-score").textContent = score + "/" + t;
          $("scan-compare").hidden = false;
        }
      })
      .catch(() => {
        // No server (index.html opened by double-click): no card saving possible.
        if (thisWait !== cardWait) return;
        setScan("expired", UI[lang].noCardTitle, "");
      });
  }

  // Skip: stop waiting for a card. (The server may still be waiting, see app.py.)
  $("skip").onclick = () => {
    cardWait++;
    setScan("expired", UI[lang].noCardTitle, "");
  };

  document
    .querySelectorAll("[data-lang]")
    .forEach((b) => (b.onclick = () => setLang(b.dataset.lang)));
  // Play again: back to the language screen, in the default left-to-right layout.
  $("again").onclick = () => {
    cardWait++; // ignore the card reply if it arrives after leaving the score screen
    document.documentElement.lang = "en";
    document.documentElement.dir = "ltr";
    show("lang");
  };
})();
