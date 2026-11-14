// Musica original, suave e acolhedora (piano + cordas), para os Reels Cotton Secrets.
// Uso: node compor.mjs <saida.mid> <variante: a|b>
import fs from "node:fs";
import MidiWriter from "midi-writer-js";

const out = process.argv[2], v = process.argv[3] || "a";
const TPB = 128, BAR = TPB * 4;
const tempo = v === "a" ? 72 : 80;

// progressoes (acordes por compasso)
const prog = v === "a"
  ? [["F3","A3","C4","E4"],["D3","F3","A3","C4"],["Bb2","D3","F3","A3"],["C3","E3","G3","Bb3"],
     ["F3","A3","C4","E4"],["A2","C3","E3","G3"],["Bb2","D3","F3","A3"],["C3","F3","G3","C4"]]
  : [["C3","E3","G3","B3"],["A2","C3","E3","G3"],["F2","A2","C3","E3"],["G2","B2","D3","F3"],
     ["C3","E3","G3","B3"],["E2","G2","B2","D3"],["F2","A2","C3","E3"],["G2","C3","D3","G3"]];
const melody = v === "a"   // [compasso, tempo(colcheias), nota, duracao em colcheias]
  ? [[4,0,"C5",3],[4,3,"A4",1],[4,4,"G4",4],[5,0,"F4",3],[5,3,"G4",1],[5,4,"A4",4],
     [6,0,"D5",3],[6,3,"C5",1],[6,4,"A4",4],[7,0,"G4",6],[7,6,"F4",2],
     [8,0,"F4",8]]
  : [[4,0,"G4",3],[4,3,"E4",1],[4,4,"D4",4],[5,0,"C4",3],[5,3,"D4",1],[5,4,"E4",4],
     [6,0,"A4",3],[6,3,"G4",1],[6,4,"E4",4],[7,0,"D4",6],[7,6,"C4",2],[8,0,"C4",8]];
const up = n => n.replace(/(\d)/, d => String(+d + 1));
const E = TPB / 2; // colcheia

const piano = new MidiWriter.Track();
piano.setTempo(tempo);
piano.addEvent(new MidiWriter.ProgramChangeEvent({ instrument: 1, channel: 1 }));
const pad = new MidiWriter.Track();
pad.addEvent(new MidiWriter.ProgramChangeEvent({ instrument: 49, channel: 2 }));
const bass = new MidiWriter.Track();
bass.addEvent(new MidiWriter.ProgramChangeEvent({ instrument: 33, channel: 3 }));

const bars = [...prog, ...prog.slice(0, 4), prog[0]];   // 13 compassos (~43s a 72bpm)
bars.forEach((ch, b) => {
  const t0 = b * BAR, last = b === bars.length - 1;
  // arpejo suave de piano: 1-3-2-4 subindo
  const arp = last ? [ch[0], ch[1], ch[2], ch[3]] : [ch[0], ch[2], ch[1], ch[3], up(ch[0]), ch[3], ch[2], ch[1]];
  arp.forEach((n, i) => piano.addEvent(new MidiWriter.NoteEvent({
    pitch: [n], tick: t0 + i * E, duration: last ? "T" + (BAR * 2) : "T" + (E * 2),
    velocity: 34 + ((i * 7) % 12), channel: 1 })));
  // cordas sustentadas
  pad.addEvent(new MidiWriter.NoteEvent({ pitch: ch.map(up), tick: t0, duration: "T" + (last ? BAR * 2 : BAR),
    velocity: 26, channel: 2 }));
  // baixo
  const root = ch[0].replace(/(\d)/, d => String(Math.max(1, +d - 1)));
  bass.addEvent(new MidiWriter.NoteEvent({ pitch: [root], tick: t0, duration: "T" + (last ? BAR * 2 : BAR),
    velocity: 38, channel: 3 }));
});
// melodia (repete a partir do compasso 9 para variantes longas)
for (const off of [0, 8]) for (const [b, e, n, d] of melody) {
  const bb = b + off; if (bb >= bars.length) continue;
  piano.addEvent(new MidiWriter.NoteEvent({ pitch: [up(n)], tick: (bb - 1 + 1) * BAR - BAR + e * E + BAR * 0,
    duration: "T" + d * E, velocity: 52, channel: 1 }));
}
const w = new MidiWriter.Writer([piano, pad, bass]);
fs.writeFileSync(out, Buffer.from(w.buildFile()));
console.log("ok", out);
