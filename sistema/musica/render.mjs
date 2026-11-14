import * as fs from "node:fs/promises";
import { audioToWav, BasicMIDI, SoundBankLoader, SpessaSynthProcessor, SpessaSynthSequencer } from "spessasynth_core";
const [sfp, midp, outp] = process.argv.slice(2);
const sf = await fs.readFile(sfp), mid = await fs.readFile(midp);
const midi = BasicMIDI.fromArrayBuffer(mid.buffer.slice(mid.byteOffset, mid.byteOffset + mid.byteLength));
const bank = SoundBankLoader.fromArrayBuffer(sf.buffer.slice(sf.byteOffset, sf.byteOffset + sf.byteLength));
const sr = 48000;
const synth = new SpessaSynthProcessor(sr, { eventsEnabled: false });
synth.soundBankManager.addSoundBank(bank, "main");
await synth.ready;
synth.setSystemParameter("autoAllocateVoices", true);
const seq = new SpessaSynthSequencer(synth);
seq.loadNewSongList([midi]); seq.play();
const n = Math.ceil(sr * (midi.duration + 4));
const L = new Float32Array(n), R = new Float32Array(n);
let f = 0;
while (f < n) { seq.processTick(); const b = Math.min(128, n - f); synth.process(L, R, f, b); f += b; }
await fs.writeFile(outp, new Uint8Array(audioToWav([L, R], sr)));
console.log("wav", outp, midi.duration.toFixed(1) + "s");
