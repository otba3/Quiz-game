(() => {
  const $ = id => document.getElementById(id);
  const stage = $('stage');

  const OUTPUT_DIR = '../../output/';  // question images live in output/images/
  const PER_GAME = 6;                   // questions per playthrough (fewer if the bank is smaller)
  const ORIGIN_PER_TYPE = 3;            // Origin: 3 continent + 3 country questions

  // Category buttons: key in QUIZ_DATA.categories -> label on screen.
  const CATEGORIES = [
    { key: 'title', name: 'Artwork Title' },
    { key: 'year', name: 'Year of Creation' },
    { key: 'origin', name: 'Geographic Origin' },
    { key: 'medium', name: 'Medium' }
  ];
  const UI = { pick: 'Choose a category', score: 'Your score', again: 'Play again',
               v: ['Try again.', 'Well played.', 'Perfect score.'] };

  let questions, i, score;

  function fit() {
    const s = Math.min(innerWidth / 1024, innerHeight / 600);
    stage.style.transform = 'translate(-50%, -50%) scale(' + s + ')';
  }
  addEventListener('resize', fit); fit();

  function show(id) {
    stage.dataset.screen = id;
    document.querySelectorAll('.screen').forEach(s => s.classList.toggle('active', s.id === id));
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
      const newDeck = shuffle(all.filter(q => !chosen.includes(q)));
      const missing = n - chosen.length;
      chosen.push(...newDeck.slice(0, missing));
      decks[deckName] = newDeck.slice(missing);
    }
    return chosen;
  }

  // Choose this game's questions.
  function pickQuestions(key) {
    const all = QUIZ_DATA.categories[key];
    if (key === 'origin') {
      const ofType = type => draw('origin-' + type, all.filter(q => q.type === type), ORIGIN_PER_TYPE);
      return shuffle(ofType('continent').concat(ofType('country')));
    }
    return draw(key, all, PER_GAME);
  }

  // Capitalise only the first letter on screen; the data keeps the API's exact text.
  const display = text => text.charAt(0).toUpperCase() + text.slice(1);

  // The question sentence, with {continent} filled in for Origin country questions.
  const questionText = q => QUIZ_DATA.texts[q.question_key].replace('{continent}', q.continent || '');

  function showCategories() {
    $('cats-title').textContent = UI.pick;
    $('end-label').textContent = UI.score;
    $('again').textContent = UI.again;
    const list = $('cat-list');
    list.innerHTML = '';
    CATEGORIES.forEach((c, n) => {
      const b = document.createElement('button');
      b.className = 'choice c' + n;
      b.textContent = c.name;
      b.onclick = () => start(c.key);
      list.appendChild(b);
    });
    show('cats');
  }

  function start(key) { questions = pickQuestions(key); i = 0; score = 0; render(); show('play'); }

  function setProgress(n) { $('fill').style.transform = 'scaleX(' + n / questions.length + ')'; }

  function render() {
    const q = questions[i];
    $('count').textContent = (i + 1) + ' / ' + questions.length;
    setProgress(i);
    $('q-text').textContent = questionText(q);
    const pic = $('pic'), img = new Image();
    img.src = OUTPUT_DIR + q.image;
    img.alt = '';
    img.onerror = () => img.remove();
    pic.innerHTML = '';
    pic.appendChild(img);
    const box = $('answers');
    box.className = 'answers';
    box.innerHTML = '';
    shuffle(q.options).forEach(text => {
      const b = document.createElement('button');
      b.className = 'ans';
      b.textContent = display(text);
      b.dataset.answer = text;  // the exact text, used to check the answer
      b.onclick = () => pick(b);
      box.appendChild(b);
    });
  }

  function pick(btn) {
    const q = questions[i], box = $('answers');
    box.classList.add('locked');
    if (btn.dataset.answer === q.answer) score++; else btn.classList.add('wrong');
    // Always highlight the correct answer, so a wrong guess still shows it.
    [...box.children].find(b => b.dataset.answer === q.answer).classList.add('correct');
    setProgress(i + 1);
    setTimeout(() => { if (++i < questions.length) render(); else finish(); }, 1200);
  }

  function finish() {
    const t = questions.length;
    $('score').innerHTML = score + '<small>/' + t + '</small>';
    $('verdict').textContent = UI.v[score === t ? 2 : score >= t / 2 ? 1 : 0];
    show('end');
  }

  document.querySelectorAll('[data-lang]').forEach(b => b.onclick = showCategories);
  $('again').onclick = () => show('lang');
})();
