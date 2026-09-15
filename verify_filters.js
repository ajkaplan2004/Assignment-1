// Verify the FINAL (3-class balanced) dashboard filter logic against its
// embedded data. Replicates the same matches()/count logic and prints counts.
const fs = require('fs');
const html = fs.readFileSync(__dirname + '/dashboard.html', 'utf8');
const m = html.match(/<script id="data" type="application\/json">([\s\S]*?)<\/script>/);
if (!m) { console.error('embedded data not found'); process.exit(1); }
const DATA = JSON.parse(m[1]);
const M = DATA.metrics, R = DATA.reviews;
const CLASSES = ['POSITIVE','NEUTRAL','NEGATIVE'];

function matches(r, F){
  if(F.verdict==='correct' && !r.correct) return false;
  if(F.verdict==='wrong' && r.correct) return false;
  if(F.pred!=='all' && r.predicted!==F.pred) return false;
  if(F.rating!=='all' && Math.round(r.rating)!==parseInt(F.rating,10)) return false;
  return true;
}
function count(F){ return R.filter(r=>matches(r,F)).length; }

// --- cross-check embedded R against step6_results json values ---
const agreeCount = R.filter(r=>r.emo_agree===true).length;
const noSignal = R.filter(r=>!r.nrc_emotion).length;
const emoDiff = R.length - agreeCount - noSignal;
console.log('embedded review count:', R.length);
console.log('embedded correct/wrong:', R.filter(r=>r.correct).length, R.filter(r=>!r.correct).length);
console.log('matches metrics? overall_acc:', M.overall_accuracy,
            'correct:', M.n_correct, 'incorrect:', M.n_incorrect);
console.log('emotion recall from rows: agree', agreeCount, 'differ', emoDiff, 'noSignal', noSignal,
            '| metric agree_count', M.emotion_agree_count, 'nrc_no_match', M.nrc_no_match);

// --- filter battery (compare where cheap to the confusion columns) ---
function colCount(cls){ return R.filter(r=>r.predicted===cls).length; }
const cases = [
  ['all', {verdict:'all',pred:'all',rating:'all'}],
  ['verdict=correct', {verdict:'correct',pred:'all',rating:'all'}],
  ['verdict=wrong', {verdict:'wrong',pred:'all',rating:'all'}],
  ['pred=POSITIVE', {verdict:'all',pred:'POSITIVE',rating:'all'}],
  ['pred=NEUTRAL', {verdict:'all',pred:'NEUTRAL',rating:'all'}],
  ['pred=NEGATIVE', {verdict:'all',pred:'NEGATIVE',rating:'all'}],
];
for(const [name,F] of cases){
  const c = count(F);
  const note = (name.startsWith('pred=')) ? ' (col total ' + colCount(name.split('=')[1]) + ')' : '';
  console.log(`${name.padEnd(18)} -> ${String(c).padStart(3)}${note}`);
}
// rating counts
const rc = {1:0,2:0,3:0,4:0,5:0};
R.forEach(r=>rc[Math.round(r.rating)]++);
console.log('rating counts:', JSON.stringify(rc));
// combined: wrong & pred=NEUTRAL
console.log('wrong & pred=NEUTRAL ->', count({verdict:'wrong',pred:'NEUTRAL',rating:'all'}));
