// Layout machinery for the v0.3 case deck. Content lives in deck.js as data;
// this file only knows how to render each layout.
const INK='1A1A16', MUTED='7A7A72', FAINT='E2E2DE', WHITE='FFFFFF';
const ACCENT='065A82';      // what the system established
const OPEN='8C4A2F';        // what remains open - a distinct hue, never "error red"
const HEAD='Cambria', BODY='Calibri', MONO='Courier New';
const M = 0.62;                       // page margin, inches
const W = 13.33, H = 7.5;

function titleBlock(s, n, total, title, kicker) {
  if (kicker) s.addText(kicker.toUpperCase(), { x:M, y:0.40, w:9.5, h:0.26, isTextBox:true, margin:0,
    fontFace:BODY, fontSize:10.5, bold:true, color:MUTED, charSpacing:1.8 });
  s.addText(title, { x:M, y: kicker?0.70:0.48, w:W-2*M-0.9, h:0.72, isTextBox:true, margin:0,
    fontFace:HEAD, fontSize:27, bold:true, color:INK });
  s.addText(`${n} / ${total}`, { x:W-M-0.9, y:0.44, w:0.9, h:0.28, isTextBox:true, margin:0,
    align:'right', fontFace:BODY, fontSize:10.5, color:MUTED });
}

// the caveat every content slide carries, sitting on its own above the foot
function caveat(s, text) {
  if (!text) return;
  s.addShape('line', { x:M, y:H-1.16, w:W-2*M, h:0, line:{color:FAINT, width:1} });
  s.addText(text, { x:M, y:H-1.06, w:W-2*M, h:0.62, isTextBox:true, margin:0, valign:'top',
    fontFace:BODY, fontSize:11.5, italic:true, color:OPEN, lineSpacingMultiple:1.18 });
}

function statRow(s, stats, y=1.95) {
  const n = stats.length, gap = 0.34;
  const w = (W - 2*M - gap*(n-1)) / n;
  stats.forEach((st, i) => {
    const x = M + i*(w+gap);
    s.addShape('line', { x, y, w, h:0, line:{color:INK, width:1.25} });
    s.addText(st.v, { x, y:y+0.16, w, h:0.95, isTextBox:true, margin:0, fontFace:HEAD,
      fontSize: st.v.length>7 ? 30 : 42, bold:true, color: st.open?OPEN:INK });
    s.addText(st.k, { x, y:y+1.16, w, h:0.95, isTextBox:true, margin:0, valign:'top', fontFace:BODY,
      fontSize:13, color:INK, lineSpacingMultiple:1.2 });
    if (st.s) s.addText(st.s, { x, y:y+2.10, w, h:0.75, isTextBox:true, margin:0, valign:'top', fontFace:BODY,
      fontSize:10.5, italic:true, color:MUTED, lineSpacingMultiple:1.15 });
  });
}

function ledger(s, cols, rows, y=1.95, sizes) {
  const widths = sizes || cols.map(() => (W-2*M)/cols.length);
  let x = M;
  cols.forEach((c, i) => {
    s.addText(c.toUpperCase(), { x, y, w:widths[i], h:0.3, isTextBox:true, margin:0,
      fontFace:BODY, fontSize:10, bold:true, color:MUTED, charSpacing:1.3 });
    x += widths[i];
  });
  s.addShape('line', { x:M, y:y+0.32, w:W-2*M, h:0, line:{color:INK, width:1.25} });
  let ry = y + 0.44;
  rows.forEach((r) => {
    let cx = M;
    const h = r.h || 0.46;
    r.cells.forEach((cell, i) => {
      s.addText(cell, { x:cx, y:ry, w:widths[i]-0.18, h, isTextBox:true, margin:0,
        fontFace: (r.mono && i===r.mono) ? MONO : BODY,
        fontSize: r.size || 12.5, bold: i===0,
        color: r.open ? OPEN : INK, lineSpacingMultiple:1.16, valign:'top' });
      cx += widths[i];
    });
    ry += h + 0.10;
    s.addShape('line', { x:M, y:ry-0.06, w:W-2*M, h:0, line:{color:FAINT, width:1} });
  });
  return ry;
}

function twoCol(s, left, right, y=1.95) {
  const cw = (W - 2*M - 0.7) / 2;
  [[left, M], [right, M+cw+0.7]].forEach(([col, x]) => {
    s.addText(col.head.toUpperCase(), { x, y, w:cw, h:0.28, isTextBox:true, margin:0,
      fontFace:BODY, fontSize:10, bold:true, color:MUTED, charSpacing:1.3 });
    s.addShape('line', { x, y:y+0.30, w:cw, h:0, line:{color:INK, width:1.25} });
    s.addText(col.body, { x, y:y+0.46, w:cw, h:3.4, isTextBox:true, margin:0, valign:'top',
      fontFace:BODY, fontSize:13, color: col.open?OPEN:INK, lineSpacingMultiple:1.28 });
  });
  s.addShape('line', { x:M+cw+0.35, y:y, w:0, h:3.6, line:{color:FAINT, width:1} });
}

function codeAndRead(s, code, read, y=1.95) {
  const cw = (W - 2*M - 0.55) * 0.52;
  s.addShape('rect', { x:M, y, w:cw, h:3.75, fill:{color:'F7F7F5'}, line:{color:FAINT, width:1} });
  s.addText(code, { x:M+0.16, y:y+0.14, w:cw-0.32, h:3.5, isTextBox:true, margin:0, valign:'top',
    fontFace:MONO, fontSize:10.5, color:INK, lineSpacingMultiple:1.22 });
  const rx = M + cw + 0.55;
  s.addText(read, { x:rx, y:y+0.04, w:W-M-rx, h:3.7, isTextBox:true, margin:0, valign:'top',
    fontFace:BODY, fontSize:13, color:INK, lineSpacingMultiple:1.3 });
}

function quote(s, text, attrib, y=2.15) {
  s.addText(text, { x:M, y, w:W-2*M, h:2.2, isTextBox:true, margin:0,
    fontFace:HEAD, fontSize:28, italic:true, color:INK, lineSpacingMultiple:1.22 });
  if (attrib) s.addText(attrib, { x:M, y:y+2.30, w:W-2*M, h:0.36, isTextBox:true, margin:0,
    fontFace:BODY, fontSize:11, color:MUTED, charSpacing:1.2 });
}

module.exports = { INK, MUTED, FAINT, WHITE, ACCENT, OPEN, HEAD, BODY, MONO, M, W, H,
                   titleBlock, caveat, statRow, ledger, twoCol, codeAndRead, quote };
