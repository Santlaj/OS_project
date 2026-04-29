const fs = await import("node:fs/promises");
const path = await import("node:path");
const { fileURLToPath } = await import("node:url");

const {
  Presentation,
  PresentationFile,
  row,
  column,
  grid,
  rule,
  text,
  fill,
  hug,
  wrap,
  fr,
  fixed,
  auto,
} = await import("@oai/artifact-tool");

const WIDTH = 1920;
const HEIGHT = 1080;

const COLORS = {
  bg: "#F8FAFC",
  bgSoft: "#ECFDF5",
  bgWarm: "#FFF7ED",
  ink: "#0F172A",
  muted: "#475569",
  teal: "#0F766E",
  orange: "#C2410C",
  blue: "#1D4ED8",
  green: "#166534",
  red: "#B91C1C",
};

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUTPUT_DIR = path.join(ROOT, "output");
const SCRATCH_DIR = path.join(ROOT, "scratch");
const PREVIEW_DIR = path.join(SCRATCH_DIR, "previews");

await fs.mkdir(OUTPUT_DIR, { recursive: true });
await fs.mkdir(PREVIEW_DIR, { recursive: true });

const presentation = Presentation.create({
  slideSize: { width: WIDTH, height: HEIGHT },
});

function titleBlock(title, subtitle, accent = COLORS.teal) {
  return column(
    { name: "title-stack", width: fill, height: hug, gap: 12 },
    [
      text(title, {
        name: "slide-title",
        width: fill,
        height: hug,
        style: { fontSize: 56, bold: true, color: COLORS.ink },
      }),
      rule({ name: "title-rule", width: fixed(220), stroke: accent, weight: 5 }),
      text(subtitle, {
        name: "slide-subtitle",
        width: wrap(1180),
        height: hug,
        style: { fontSize: 26, color: COLORS.muted },
      }),
    ],
  );
}

function bigText(value, width = 760, color = COLORS.ink) {
  return text(value, {
    width: wrap(width),
    height: hug,
    style: { fontSize: 40, bold: true, color },
  });
}

function bodyText(value, width = 780, color = COLORS.muted, size = 28) {
  return text(value, {
    width: wrap(width),
    height: hug,
    style: { fontSize: size, color },
  });
}

function noteText(value, width = 900) {
  return text(value, {
    width: wrap(width),
    height: hug,
    style: { fontSize: 22, color: COLORS.muted },
  });
}

function stepRow(number, value, accent = COLORS.teal) {
  return row(
    { width: fill, height: hug, gap: 24, align: "start" },
    [
      text(number, {
        width: fixed(90),
        height: hug,
        style: { fontSize: 42, bold: true, color: accent },
      }),
      text(value, {
        width: fill,
        height: hug,
        style: { fontSize: 28, color: COLORS.ink },
      }),
    ],
  );
}

function tableRow(left, right, isHeader = false) {
  return row(
    { width: fill, height: hug, gap: 28 },
    [
      text(left, {
        width: fixed(620),
        height: hug,
        style: {
          fontSize: isHeader ? 24 : 26,
          bold: isHeader,
          color: isHeader ? COLORS.teal : COLORS.ink,
        },
      }),
      text(right, {
        width: fill,
        height: hug,
        style: {
          fontSize: isHeader ? 24 : 26,
          bold: isHeader,
          color: isHeader ? COLORS.teal : COLORS.muted,
        },
      }),
    ],
  );
}

function addSlide(bg = COLORS.bg) {
  const slide = presentation.slides.add();
  slide.background.fill = bg;
  return slide;
}

{
  const slide = addSlide(COLORS.bgSoft);
  slide.compose(
    column(
      {
        name: "cover-root",
        width: fill,
        height: fill,
        padding: { x: 110, y: 90 },
        gap: 34,
      },
      [
        text("Bistable\nMultivibrator", {
          name: "hero-title",
          width: wrap(880),
          height: hug,
          style: { fontSize: 78, bold: true, color: COLORS.ink },
        }),
        rule({ name: "hero-rule", width: fixed(260), stroke: COLORS.orange, weight: 6 }),
        text("Simple English PPT", {
          name: "hero-chip",
          width: fill,
          height: hug,
          style: { fontSize: 30, bold: true, color: COLORS.teal },
        }),
        text(
          "A bistable multivibrator is a circuit that has two stable states. It works like a basic memory element and is also called a flip-flop.",
          {
            name: "hero-subtitle",
            width: wrap(980),
            height: hug,
            style: { fontSize: 30, color: COLORS.muted },
          },
        ),
        text("Prepared in simple classroom language", {
          name: "hero-footer",
          width: fill,
          height: hug,
          style: { fontSize: 22, color: COLORS.muted },
        }),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

{
  const slide = addSlide();
  slide.compose(
    column(
      {
        name: "root",
        width: fill,
        height: fill,
        padding: { x: 90, y: 72 },
        gap: 36,
      },
      [
        titleBlock("What Is A Bistable Multivibrator?", "It stays in one of two stable conditions until a trigger changes it."),
        row(
          { width: fill, height: fill, gap: 72 },
          [
            bigText("It is an electronic circuit that can remember one of two output states.", 720),
            column(
              { width: fill, height: hug, gap: 22 },
              [
                bodyText("- It has two stable states.", 760),
                bodyText("- It stores one bit of information.", 760),
                bodyText("- It changes state only when a trigger pulse is applied.", 760),
                bodyText("- Another common name is flip-flop.", 760),
              ],
            ),
          ],
        ),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

{
  const slide = addSlide("#F0F9FF");
  slide.compose(
    column(
      {
        name: "root",
        width: fill,
        height: fill,
        padding: { x: 90, y: 72 },
        gap: 36,
      },
      [
        titleBlock("The Two Stable States", "The output can stay in either state for a long time.", COLORS.blue),
        row(
          { width: fill, height: fill, gap: 90 },
          [
            column(
              { width: fill, height: hug, gap: 20 },
              [
                bigText("State 1", 480, COLORS.blue),
                bodyText("Q = 1 and Q' = 0", 560, COLORS.ink, 30),
                bodyText("The first side is ON and the second side is OFF.", 620),
                bodyText("The circuit keeps this state until another pulse comes.", 620),
              ],
            ),
            column(
              { width: fill, height: hug, gap: 20 },
              [
                bigText("State 2", 480, COLORS.orange),
                bodyText("Q = 0 and Q' = 1", 560, COLORS.ink, 30),
                bodyText("The second side is ON and the first side is OFF.", 620),
                bodyText("This state also stays fixed until a new trigger is given.", 620),
              ],
            ),
          ],
        ),
        noteText("Important point: the circuit remembers its last state. That is why it is used as a memory element."),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

{
  const slide = addSlide("#FFFBEB");
  slide.compose(
    column(
      {
        name: "root",
        width: fill,
        height: fill,
        padding: { x: 90, y: 72 },
        gap: 30,
      },
      [
        titleBlock("How Does It Work?", "Simple step-by-step working of the circuit.", COLORS.orange),
        column(
          { width: fill, height: hug, gap: 18 },
          [
            stepRow("01", "Power is applied to the circuit.", COLORS.orange),
            stepRow("02", "Because of feedback, one side becomes stronger and turns ON first.", COLORS.orange),
            stepRow("03", "A set pulse can move the circuit to one stable state.", COLORS.orange),
            stepRow("04", "A reset pulse can move it to the other stable state.", COLORS.orange),
            stepRow("05", "Without a new pulse, the output stays unchanged.", COLORS.orange),
          ],
        ),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

{
  const slide = addSlide();
  slide.compose(
    column(
      {
        name: "root",
        width: fill,
        height: fill,
        padding: { x: 90, y: 72 },
        gap: 28,
      },
      [
        titleBlock("Set And Reset Action", "This is the simple behavior of a basic SR bistable multivibrator."),
        tableRow("Input condition", "Result", true),
        rule({ width: fill, stroke: "#CBD5E1", weight: 2 }),
        tableRow("Set input is active", "Q becomes 1 and the circuit goes to the set state."),
        rule({ width: fill, stroke: "#E2E8F0", weight: 1 }),
        tableRow("Reset input is active", "Q becomes 0 and the circuit goes to the reset state."),
        rule({ width: fill, stroke: "#E2E8F0", weight: 1 }),
        tableRow("No input pulse", "The previous state remains stored."),
        rule({ width: fill, stroke: "#E2E8F0", weight: 1 }),
        tableRow("Both inputs active together", "This condition is usually avoided in a basic SR circuit."),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

{
  const slide = addSlide("#F0FDF4");
  slide.compose(
    column(
      {
        name: "root",
        width: fill,
        height: fill,
        padding: { x: 90, y: 72 },
        gap: 34,
      },
      [
        titleBlock("Main Circuit Idea", "Feedback between two sections creates the two stable states.", COLORS.green),
        row(
          { width: fill, height: fill, gap: 64 },
          [
            bigText("Output of one side goes to the other side, and the second side feeds back again.", 760, COLORS.green),
            column(
              { width: fill, height: hug, gap: 22 },
              [
                bodyText("- It may be built using transistors or logic gates.", 760),
                bodyText("- Cross-coupled feedback keeps the state stable.", 760),
                bodyText("- A trigger pulse breaks the old balance and makes a new state.", 760),
                bodyText("- That is why the circuit acts like a small memory unit.", 760),
              ],
            ),
          ],
        ),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

{
  const slide = addSlide("#EFF6FF");
  slide.compose(
    column(
      {
        name: "root",
        width: fill,
        height: fill,
        padding: { x: 90, y: 72 },
        gap: 34,
      },
      [
        titleBlock("Applications", "Where a bistable multivibrator is used.", COLORS.blue),
        grid(
          {
            width: fill,
            height: hug,
            columns: [fr(1), fr(1)],
            rows: [auto, auto],
            columnGap: 56,
            rowGap: 34,
          },
          [
            column(
              { width: fill, height: hug, gap: 10 },
              [
                bigText("Memory circuits", 440, COLORS.blue),
                bodyText("Used to store one bit of data in digital systems.", 520),
              ],
            ),
            column(
              { width: fill, height: hug, gap: 10 },
              [
                bigText("Counters", 440, COLORS.blue),
                bodyText("Helps in counting pulses in electronic devices.", 520),
              ],
            ),
            column(
              { width: fill, height: hug, gap: 10 },
              [
                bigText("Switch debouncing", 440, COLORS.blue),
                bodyText("Removes false switching caused by noisy push buttons.", 520),
              ],
            ),
            column(
              { width: fill, height: hug, gap: 10 },
              [
                bigText("Registers and control circuits", 520, COLORS.blue),
                bodyText("Used in many digital control and storage blocks.", 520),
              ],
            ),
          ],
        ),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

{
  const slide = addSlide();
  slide.compose(
    column(
      {
        name: "root",
        width: fill,
        height: fill,
        padding: { x: 90, y: 72 },
        gap: 34,
      },
      [
        titleBlock("Advantages And Limitations", "A short summary for revision."),
        row(
          { width: fill, height: fill, gap: 72 },
          [
            column(
              { width: fill, height: hug, gap: 18 },
              [
                bigText("Advantages", 420, COLORS.green),
                bodyText("- Simple and easy to understand.", 560),
                bodyText("- Stores one bit of information.", 560),
                bodyText("- Gives a stable output.", 560),
                bodyText("- Very useful in digital electronics.", 560),
              ],
            ),
            column(
              { width: fill, height: hug, gap: 18 },
              [
                bigText("Limitations", 420, COLORS.red),
                bodyText("- Needs a trigger pulse to change state.", 620),
                bodyText("- Basic SR type has an unwanted input condition.", 620),
                bodyText("- It is not used for continuous oscillation.", 620),
              ],
            ),
          ],
        ),
        noteText("Conclusion: a bistable multivibrator is a two-state memory circuit and is one of the basic building blocks of digital electronics."),
      ],
    ),
    { frame: { left: 0, top: 0, width: WIDTH, height: HEIGHT }, baseUnit: 8 },
  );
}

const pptxPath = path.join(OUTPUT_DIR, "output.pptx");
const pptxBlob = await PresentationFile.exportPptx(presentation);
await pptxBlob.save(pptxPath);

for (const slide of presentation.slides.items) {
  const index = String(slide.index + 1).padStart(2, "0");
  const pngBlob = await slide.export({ format: "png", scale: 1 });
  await pngBlob.save(path.join(PREVIEW_DIR, `slide-${index}.png`));
}

console.log(
  JSON.stringify(
    {
      pptx: pptxPath,
      previews: PREVIEW_DIR,
      slideCount: presentation.slides.items.length,
    },
    null,
    2,
  ),
);
