---
name: "character-sheet-cropped-front"
description: "Use instead of character-creation for every character reference sheet prompt: 3 panels — front full-body with the head cleanly removed (same scale as the back view), full back view, tight face close-up. Georgian or English input."
---

# Character Sheet — Headless Front Reference Prompt

Use this skill when the user wants a character reference sheet / turnaround / character design prompt for image generation, pastes a character description, or supplies a reference image and asks for a character sheet (clean or with a story condition: wounds, dirt, wear, wetness, etc.). It replaces the older character-creation layout. The only difference: in the FRONT full-body panel the head is cleanly removed, while the figure keeps exactly the same size, framing and height as in the BACK panel.

## Output

1. One complete English prompt in a single code block, built from the template below, with every placeholder filled in and unused optional sections removed.
2. After it, 2–4 short notes in the user's language (usually Georgian) covering only: choices you made where the input was open, and anything to check in the result (e.g. mark side, mirroring, front figure smaller or cropped differently than the back, head or neck flesh still visible in the front panel).

No headings or long explanations beyond that. Keep it concise.

## Two modes

- **Reference image provided (default when the user attaches or mentions one):** do NOT write the CHARACTER / HAIR / CLOTHING appearance blocks. Use only the character's name and the identity lock line. Appearance comes from the reference. Describe only what the reference cannot show (missing garments/footwear) and the CONDITION.
- **Text description only, no reference:** fill the optional CHARACTER, HAIR & FACIAL HAIR, CLOTHING, DISTINCTIVE MARK and HANDS & ACCESSORIES blocks from the description, and delete the reference identity-lock line.

## Filling rules

- **Layout is fixed:** exactly three panels — FRONT full body (head removed), BACK full body, frontal FACE CLOSE-UP. Never side, profile or 3/4 views.
- **Front panel = same framing as the back panel, head cleanly removed.** The camera distance, figure scale, feet position and floor line are identical to the back panel; the figure is NOT zoomed in and NOT pushed up so the frame edge cuts it. The panel keeps the same empty headroom above the shoulders as the back panel. Only the head (and neck above the collar) is removed: a clean, precise cut at the top of the collar / neckline / gorget, and the seamless grey backdrop shows where the head would be. The collar opening may show its dark inner lining or padding. No neck stump, no skin, no blood or anatomy at the cut, no ragged or blurred edge. The body below keeps natural human volume, posture and weight — shoulders and chest filled out as if worn — only the head is missing.
- **Back panel = entire figure head to feet**, nothing cropped (head and back of the hair visible). Its framing is the reference for the front panel.
- **Face close-up = the face only, as tight as possible.** Frontal, looking straight into the camera, an extreme close-up where the face fills the entire panel edge to edge: framed from the hairline / top of the forehead down to just below the chin (the top of the hair may be slightly cropped). NO shoulders, NO neck below the chin, NO collar or clothing in this panel. All focus and detail on the face itself — skin texture, eyes, facial marks and the condition on the face.
- **Use only what the input says, plus minimal neutral defaults.** Where something is open (age, hair, missing garment), choose one sensible option that fits the era/role and mention it in the notes.
- **Pick one option, never two.** If the input says "brown or charcoal", choose one and say in the notes how to switch it.
- **Missing garments:** anything not visible in the reference (lower garment, shoes) gets a plain, modest, context-appropriate default — nothing stylish.
- **Condition logic:** every mark must have a physical cause from the story and appear only where that cause would leave it. The side that took the action (crawling, falling, leaning) carries the heavy marks; the opposite side only light traces. Accessory and clothing damage (cracks, tears, creases, stains) matches the same cause. Blood: mix of dried darkened and fresh, runs downward with gravity, soaks into fabric. Always medically accurate and documentary, never gore. For a clean character write "clean, neutral, undamaged" and delete the condition rules.
- **Face condition goes to the close-up.** Because the front panel has no head, every facial mark (cuts, bruises, dirt, blood on the face) is described for the close-up; blood that ran from the face down onto the collar or chest may still show on the clothing in the front panel.
- **Side logic (critical):** describe marks, wounds and accessories by the character's OWN side and add in parentheses which side they appear on for the viewer in the front panel and close-up (always the opposite). Add the wrong side / wrong hand to NEGATIVE.
- **Excluded items:** add character-specific exclusions to NEGATIVE (e.g. rank vestments when rank isn't stated, modern grooming for historical characters, jewellery not in the reference).
- **Lighting stays neutral studio** for the sheet, even if the scene uses candle or dramatic light; mention this in the notes only if the user specified scene lighting.
- **Don't write scene behaviour** (sitting, writing, gestures) — body panels are a neutral standing pose, arms relaxed at the sides. Emotional state goes only into the expression.
- **Changes:** when the user asks for changes, apply them and return the full corrected prompt, never partial "replace this line" instructions.
- Default aspect ratio 16:9 unless the user says otherwise.

## Template

```
Ultra-realistic photographic character reference sheet of [CHARACTER NAME]. Use the reference image for face AND clothing — keep identity, face, hair, age, body proportions, accessories and every visible garment 100% identical to the reference. Any garment or footwear not visible in the reference: [MISSING ITEMS — e.g. simple plain trousers and worn everyday shoes], plain and period/context-appropriate, nothing stylish. Do not redesign or add anything else. Only add the condition described below.

LAYOUT: exactly THREE panels side by side, nothing else — no side view, no profile, no 3/4 view:
1. FRONT — full body facing the camera straight on, framed EXACTLY like the back panel: same camera distance, same figure size and height, same feet position and floor line, same empty headroom above the shoulders; the whole figure fits inside the frame, feet not cropped. The HEAD IS CLEANLY REMOVED: a precise, clean cut at the top of the [COLLAR / NECKLINE / GORGET], and the seamless grey backdrop is visible where the head would be. The collar opening shows only its dark inner [LINING / PADDING]. No neck stump, no skin, no blood or anatomy at the cut. The body keeps natural human volume and posture, shoulders and chest filled out as worn. Arms relaxed at the sides.
2. BACK — full body, seen straight from behind, entire figure visible from head to feet, nothing cropped, head and back of the hair visible. Same pose, same scale as the front panel.
3. FACE CLOSE-UP — extreme frontal close-up of the FACE ONLY, looking straight into the camera. The face fills the entire panel edge to edge, framed tightly from the hairline / top of the forehead down to just below the chin; the top of the hair may be slightly cropped. No shoulders, no neck below the chin, no collar or clothing visible. All focus on the face: eyes, skin texture, pores, facial marks and condition sharp and detailed. [EXPRESSION] expression.

[OPTIONAL — text-only mode, no reference]
CHARACTER: [ETHNICITY/ORIGIN] [MAN/WOMAN], about [AGE RANGE] years old, [ROLE + ERA/SETTING]. [BUILD + HEIGHT]. [FACE SHAPE], [NOSE], [LIPS/JAW], natural facial asymmetry. [SKIN TONE], [AGE MARKS]. [EYE COLOUR] eyes. [EYEBROWS].
HAIR & FACIAL HAIR: [HAIR COLOUR], [STYLE + LENGTH]. [BEARD/MOUSTACHE or "clean-shaven"]. [HEADWEAR or "No headwear"].
CLOTHING: [GARMENT TYPE], [COLOUR], [FABRIC + TEXTURE], [CUT], natural folds, [WEAR LEVEL]. [FOOTWEAR]. No [EXCLUDED DECORATION].
DISTINCTIVE MARK: [MARK] on [HIS/HER] [LEFT/RIGHT] [LOCATION] (character's own [LEFT/RIGHT] — viewer's [OPPOSITE] in the front panel and close-up), subtle and natural.
HANDS & ACCESSORIES: [ACCESSORY] on the [LEFT/RIGHT] hand's [FINGER] (viewer's [OPPOSITE] in the front panel).
[END OPTIONAL]

CONDITION: [injuries, dirt, wear, wetness, etc. by body area — front body, back, and face (face marks shown in the close-up) — or "clean, neutral, undamaged"]
Rules for any condition:
- Every mark has a physical cause from the story ([CAUSE]) and appears only where that cause would logically leave it
- Front and back are consistent: the side that took the action carries the heavy marks, the other side only light traces
- Damage to accessories and clothing (cracks, tears, creases, stains) matches the same cause
- Blood (if any) is a mix of dried darkened and fresh, runs downward with gravity, soaks into fabric realistically
- Realistic and medically accurate, documentary, not gore — no exposed flesh, no deep gashes

CONSISTENCY: identical face, hair, body proportions, outfit, accessories, marks and condition across all three panels; front and back figures are the same size and stand on the same floor line.

PHOTOGRAPHY: shot on IMAX 70mm film camera, f/8, real human skin with pores, wrinkles, fine hairs and natural imperfections appropriate to age. Soft, even studio lighting with a subtle rim light so all textures, stains and details read clearly on both light and dark fabrics. Soft natural contact shadows on the floor. [ASPECT RATIO].

BACKGROUND: clean, seamless light grey studio backdrop, no props, no text, no labels.

NEGATIVE: NO side view, NO profile, NO 3/4 view, NO CGI, NO 3D render, NO illustration, NO plastic or waxy skin, NO airbrushing, NO crushed blacks, NO gore, NO cartoonish bright-red blood, NO head, face, chin or neck skin in the front panel, NO neck stump or anatomy at the cut, NO front figure zoomed in, larger, or cropped by the top frame edge, NO front panel framed differently from the back panel, NO cropped feet in either full-body panel, NO cropped head in the back panel, NO shoulders, neck, collar or clothing in the face close-up, NO medium or head-and-shoulders framing in the face panel, NO mirrored or flipped panels, NO text or watermarks, NO changes to face, hair, accessories or clothing design, [MARK/ACCESSORY ON THE WRONG SIDE], [CHARACTER-SPECIFIC EXCLUSIONS].
```

## Example (abbreviated)

Input: reference image of a battle-worn medieval knight (plate armour over mail, torn dark tabard, short hair, full beard); fought on foot, took blows to the head and chest, fell in mud.

Key fills: CHARACTER NAME = the knight; COLLAR = steel gorget; LINING = dark quilted padding; MISSING ITEMS = none; EXPRESSION = exhausted, grim, focused; CAUSE = sword blows and a fall into mud; CONDITION front body = dents and scratches on breastplate and pauldrons, smeared dried and fresh blood on the chest plate, mud splashed up the legs and tabard hem; CONDITION back = lighter mud and dust, a few scratches on the backplate; face (close-up) = cut on the forehead with blood running down, swollen black eye on his own left (viewer's right), dirt and sweat in the beard; front panel at the same scale as the back, head cleanly removed at the top of the gorget with grey backdrop above; appearance blocks omitted (reference mode).