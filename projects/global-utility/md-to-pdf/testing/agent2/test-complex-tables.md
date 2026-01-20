# Complex Tables Test

## Test 1: Multi-column table with varying content lengths

| Column 1 | Column 2 | Column 3 | Column 4 | Column 5 |
|----------|----------|----------|----------|----------|
| Short | Medium length text | This is a very long text that should wrap within the cell and test how the table handles overflow content | Value | Data |
| A | B | C | D | E |
| 12345 | Lorem ipsum dolor sit amet | X | Y | Z |
| Test | Another row with mixed content lengths | Short | Very long description that goes on and on and should test wrapping behavior | End |

## Test 2: Table with alignment variations

| Left Aligned | Center Aligned | Right Aligned | Default |
|:-------------|:--------------:|--------------:|---------|
| Left | Center | Right | Default |
| Apple | 100 | $5.99 | Green |
| Banana | 200 | $3.49 | Yellow |
| Cherry | 50 | $12.99 | Red |

## Test 3: Table with special characters and formatting

| Feature | Description | Status | Notes |
|---------|-------------|--------|-------|
| **Bold Text** | `code inline` | ✅ Done | Works well |
| *Italic* | [Link](https://example.com) | 🔄 In Progress | Testing... |
| ~~Strikethrough~~ | Mixed **bold** and *italic* | ❌ Failed | Needs fix |
| Unicode: 你好 | Emoji: 🚀🎉💯 | ⚠️ Warning | Special chars |

## Test 4: Wide table with many columns

| Col1 | Col2 | Col3 | Col4 | Col5 | Col6 | Col7 | Col8 | Col9 | Col10 |
|------|------|------|------|------|------|------|------|------|-------|
| A1 | B1 | C1 | D1 | E1 | F1 | G1 | H1 | I1 | J1 |
| A2 | B2 | C2 | D2 | E2 | F2 | G2 | H2 | I2 | J2 |
| A3 | B3 | C3 | D3 | E3 | F3 | G3 | H3 | I3 | J3 |

## Test 5: Narrow table with very wide content

| Item | Description |
|------|-------------|
| Test 1 | This is an extremely long description that contains a lot of text and should definitely cause wrapping issues if the table doesn't handle overflow properly. It includes multiple sentences and goes on for quite a while to really stress test the rendering capabilities. |
| Test 2 | Another long entry with a URL: https://www.example.com/very/long/path/to/some/resource/that/might/cause/problems/with/table/formatting |
| Test 3 | Code example: `const veryLongVariableName = someFunctionWithALongName(parameterOne, parameterTwo, parameterThree, parameterFour);` |

## Test 6: Empty cells and minimal content

| A | B | C |
|---|---|---|
| X |   | Z |
|   | Y |   |
| 1 | 2 | 3 |
|   |   |   |

## Test 7: Numbers and calculations

| Item | Quantity | Unit Price | Subtotal | Tax (10%) | Total |
|------|----------|------------|----------|-----------|-------|
| Widget A | 5 | $19.99 | $99.95 | $9.99 | $109.94 |
| Widget B | 10 | $7.50 | $75.00 | $7.50 | $82.50 |
| Widget C | 2 | $149.99 | $299.98 | $29.99 | $329.97 |
| **TOTAL** | **17** | - | **$474.93** | **$47.48** | **$522.41** |
