import { jsPDF } from 'jspdf';

export const DMI_RATION_EXPLANATION =
  'Predicted dry-matter intake and advisory ration quantity are different measures. Dry-matter intake represents feed material after moisture is excluded. The advisory ration is generated separately by the FarmLite nutrition rule engine. FarmLite does not convert the DMI prediction into roughage, concentrate or fresh-feed quantities.';

export const FARMER_ADVISORY_DISCLAIMER =
  'This recommendation is advisory and should not replace guidance from a veterinarian or qualified animal nutritionist.';

export interface FarmerRecommendationPdfData {
  generatedAt: Date;
  animal: {
    name: string;
    tag: string;
    breed: string;
    ageMonths: string;
    weightKg: string;
    lactationStage: string;
    healthStatus: string;
    daysInMilk: string;
    previousWeekAvgYieldL: string;
    bodyConditionScore: string;
    ambientTemperatureC: string;
    humidityPercent: string;
    geneticGroupLabel: string;
  };
  expectedMilkYieldLDay: number | null;
  predictedDmiKgDay: number | null;
  calculatedThi: number | null;
  thiCategory: string | null;
  ration: {
    totalKgDay: number | null;
    roughageKgDay: number | null;
    concentrateKgDay: number | null;
    mineralMixKgDay: number | null;
    waterAdvice: string;
    feedingFrequency: string;
    confidenceLevel: string;
  };
  ruleExplanation: string[];
  cowAndRationWarnings: string[];
  dmiScopeMessage: string;
  limitations: string[];
}

export interface FarmerPdfContent {
  title: string;
  cowSummary: Array<[string, string]>;
  primaryResults: Array<{
    label: string;
    value: string;
    source: string;
  }>;
  rationBreakdown: Array<[string, string]>;
  explanation: string[];
  warnings: string[];
  aiModelScope: string[];
  valueSources: string[];
  technicalSourceNotes: string[];
  limitations: string[];
  disclaimer: string;
}

const finiteOrNull = (value: number | null): number | null =>
  value !== null && Number.isFinite(value) ? value : null;

const formatNumber = (
  value: number | null,
  maximumFractionDigits = 2
): string => {
  const finite = finiteOrNull(value);
  if (finite === null) return 'Unavailable';
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits,
  }).format(finite);
};

const withUnit = (value: number | null, unit: string): string => {
  const formatted = formatNumber(value);
  return formatted === 'Unavailable' ? formatted : `${formatted} ${unit}`;
};

const displayText = (value: string, fallback = 'Unavailable'): string =>
  value.trim() || fallback;

const formNumberWithUnit = (value: string, unit: string): string => {
  if (!value.trim()) return 'Unavailable';
  const parsed = Number(value);
  return Number.isFinite(parsed) ? `${formatNumber(parsed)} ${unit}` : 'Unavailable';
};

const uniqueText = (values: string[]): string[] =>
  Array.from(new Set(values.map((value) => value.trim()).filter(Boolean)));

export const buildFarmerPdfContent = (
  data: FarmerRecommendationPdfData
): FarmerPdfContent => {
  const thi = finiteOrNull(data.calculatedThi);
  const thiValue =
    thi === null
      ? 'Unavailable'
      : `${formatNumber(thi)} - ${data.thiCategory ?? 'Unavailable'}`;
  const warnings = uniqueText(data.cowAndRationWarnings);

  return {
    title: 'FarmLite Feed and Production Decision-Support Report',
    cowSummary: [
      ['Breed', displayText(data.animal.breed)],
      ['Age', formNumberWithUnit(data.animal.ageMonths, 'months')],
      ['Weight', formNumberWithUnit(data.animal.weightKg, 'kg')],
      ['Lactation stage', displayText(data.animal.lactationStage)],
      ['Health status', displayText(data.animal.healthStatus)],
      ['Days in milk', displayText(data.animal.daysInMilk)],
      [
        'Previous-week average yield',
        data.animal.previousWeekAvgYieldL.trim()
          ? `${data.animal.previousWeekAvgYieldL} L`
          : 'Unavailable',
      ],
      ['Body-condition score', displayText(data.animal.bodyConditionScore)],
      [
        'Temperature',
        data.animal.ambientTemperatureC.trim()
          ? `${data.animal.ambientTemperatureC} C`
          : 'Unavailable',
      ],
      [
        'Humidity',
        data.animal.humidityPercent.trim()
          ? `${data.animal.humidityPercent}%`
          : 'Unavailable',
      ],
      ['Genetic group', displayText(data.animal.geneticGroupLabel)],
    ],
    primaryResults: [
      {
        label: 'Expected Milk Yield',
        value: withUnit(data.expectedMilkYieldLDay, 'L/day'),
        source: 'FarmLite milk prediction model',
      },
      {
        label: 'Predicted Dry-Matter Intake',
        value: withUnit(data.predictedDmiKgDay, 'kg DM/cow/day'),
        source: 'Collected-data DMI model',
      },
      {
        label: 'Heat Stress Index',
        value: thiValue,
        source: 'Backend THI calculation',
      },
      {
        label: 'Advisory Daily Ration',
        value: withUnit(data.ration.totalKgDay, 'kg/day'),
        source: 'FarmLite nutrition rule engine',
      },
    ],
    rationBreakdown: [
      ['Roughage', withUnit(data.ration.roughageKgDay, 'kg/day')],
      ['Concentrate', withUnit(data.ration.concentrateKgDay, 'kg/day')],
      ['Mineral mix', withUnit(data.ration.mineralMixKgDay, 'kg/day')],
      ['Water advice', displayText(data.ration.waterAdvice)],
      ['Feeding frequency', displayText(data.ration.feedingFrequency)],
      ['Confidence level', displayText(data.ration.confidenceLevel)],
    ],
    explanation: uniqueText([
      data.ruleExplanation[0] ??
        'Feed quantities are generated by the FarmLite nutrition rule engine.',
      DMI_RATION_EXPLANATION,
    ]),
    warnings:
      warnings.length > 0
        ? warnings
        : [
            'No cow or ration warnings were identified for the supplied inputs.',
          ],
    aiModelScope: [
      'AI estimates are decision-support values and are not guaranteed outcomes. The DMI model was developed using a collected research dataset and requires wider multi-farm validation.',
      displayText(data.dmiScopeMessage),
    ],
    valueSources: [
      'Expected milk yield: FarmLite milk prediction model',
      'Dry-matter intake: Collected-data DMI model',
      'Heat Stress Index: Backend THI calculation',
      'Advisory ration: FarmLite nutrition rule engine',
    ],
    technicalSourceNotes: [
      'DMI research-data source: Mendeley Data, DOI: 10.17632/954f6g36sb.2',
    ],
    limitations: uniqueText(data.limitations),
    disclaimer: FARMER_ADVISORY_DISCLAIMER,
  };
};

const palette = {
  dark: [40, 54, 24] as const,
  green: [96, 108, 56] as const,
  cream: [254, 250, 224] as const,
  tan: [221, 161, 94] as const,
  orange: [188, 108, 37] as const,
  gray: [75, 85, 99] as const,
  lightGray: [229, 231, 235] as const,
  white: [255, 255, 255] as const,
};

export const createFarmerRecommendationPdf = (
  data: FarmerRecommendationPdfData
): jsPDF => {
  const content = buildFarmerPdfContent(data);
  const report = new jsPDF();
  const pageWidth = report.internal.pageSize.getWidth();
  const pageHeight = report.internal.pageSize.getHeight();
  const margin = 14;
  const contentWidth = pageWidth - margin * 2;

  const drawPageHeader = (subtitle: string) => {
    report.setFillColor(...palette.dark);
    report.roundedRect(margin, 12, contentWidth, 25, 3, 3, 'F');
    report.setTextColor(...palette.white);
    report.setFont('helvetica', 'bold');
    report.setFontSize(16);
    report.text('FarmLite', margin + 6, 22);
    report.setFontSize(11);
    report.text(subtitle, margin + 6, 30);
    report.setTextColor(...palette.dark);
  };

  const drawSectionHeading = (title: string, y: number): number => {
    report.setFillColor(...palette.green);
    report.roundedRect(margin, y, contentWidth, 8, 2, 2, 'F');
    report.setTextColor(...palette.white);
    report.setFont('helvetica', 'bold');
    report.setFontSize(10);
    report.text(title, margin + 4, y + 5.5);
    report.setTextColor(...palette.dark);
    return y + 12;
  };

  const drawGrid = (
    rows: Array<[string, string]>,
    startY: number,
    columns = 2
  ): number => {
    const gap = 5;
    const cellWidth = (contentWidth - gap * (columns - 1)) / columns;
    const rowHeight = 10;
    rows.forEach(([label, value], index) => {
      const column = index % columns;
      const row = Math.floor(index / columns);
      const x = margin + column * (cellWidth + gap);
      const y = startY + row * rowHeight;
      report.setFillColor(...palette.cream);
      report.setDrawColor(...palette.tan);
      report.roundedRect(x, y, cellWidth, 9.3, 1.5, 1.5, 'FD');
      report.setFont('helvetica', 'bold');
      report.setFontSize(7.5);
      report.setTextColor(...palette.gray);
      report.text(`${label}:`, x + 2.5, y + 3.2);
      report.setFont('helvetica', 'normal');
      report.setTextColor(...palette.dark);
      const lines = report.splitTextToSize(value, cellWidth - 4);
      report.text(lines.slice(0, 2), x + 2.5, y + 6.2);
    });
    return startY + Math.ceil(rows.length / columns) * rowHeight;
  };

  const drawResultCards = (startY: number): number => {
    const gap = 6;
    const cardWidth = (contentWidth - gap) / 2;
    const cardHeight = 29;
    content.primaryResults.forEach((result, index) => {
      const column = index % 2;
      const row = Math.floor(index / 2);
      const x = margin + column * (cardWidth + gap);
      const y = startY + row * (cardHeight + gap);
      const cardFill =
        index % 2 === 0 ? palette.cream : palette.white;
      report.setFillColor(cardFill[0], cardFill[1], cardFill[2]);
      report.setDrawColor(...palette.tan);
      report.roundedRect(x, y, cardWidth, cardHeight, 2.5, 2.5, 'FD');
      report.setTextColor(...palette.dark);
      report.setFont('helvetica', 'bold');
      report.setFontSize(9);
      report.text(result.label, x + 4, y + 7);
      report.setFontSize(13);
      report.text(result.value, x + 4, y + 15);
      report.setFont('helvetica', 'normal');
      report.setFontSize(7.5);
      report.setTextColor(...palette.green);
      report.text(`Source: ${result.source}`, x + 4, y + 23);
    });
    return startY + cardHeight * 2 + gap;
  };

  const drawTextLines = (
    values: string[],
    startY: number,
    options: { bullets?: boolean; fontSize?: number } = {}
  ): number => {
    let y = startY;
    const fontSize = options.fontSize ?? 8.5;
    const lineHeight = fontSize * 0.43;
    report.setFont('helvetica', 'normal');
    report.setFontSize(fontSize);
    report.setTextColor(...palette.dark);
    values.forEach((value) => {
      const prefix = options.bullets ? '- ' : '';
      const lines = report.splitTextToSize(
        `${prefix}${value}`,
        contentWidth - (options.bullets ? 4 : 0)
      );
      report.text(lines, margin + (options.bullets ? 2 : 0), y);
      y += lines.length * lineHeight + 2;
    });
    return y;
  };

  drawPageHeader(content.title);
  report.setFont('helvetica', 'normal');
  report.setFontSize(8);
  report.setTextColor(...palette.gray);
  report.text(
    `Generated: ${data.generatedAt.toLocaleString()}`,
    margin,
    42
  );
  report.text(
    `Cow: ${displayText(data.animal.name)}  |  Tag: ${displayText(data.animal.tag)}`,
    pageWidth - margin,
    42,
    { align: 'right' }
  );

  let y = drawSectionHeading('Selected Cow Summary', 47);
  y = drawGrid(content.cowSummary, y);
  y = drawSectionHeading('Primary Results', y + 2);
  y = drawResultCards(y);
  y = drawSectionHeading('Ration Breakdown', y + 2);
  y = drawGrid(content.rationBreakdown, y);
  y = drawSectionHeading('Explanation', y + 2);
  drawTextLines(content.explanation, y, { fontSize: 8 });

  report.addPage();
  drawPageHeader('Decision-Support Notes');
  y = drawSectionHeading('Cow and Ration Warnings', 44);
  y = drawTextLines(content.warnings, y, { bullets: true });
  y = drawSectionHeading('AI Model Scope', y + 2);
  y = drawTextLines(content.aiModelScope, y);
  y = drawSectionHeading('Value Sources', y + 2);
  y = drawTextLines(content.valueSources, y, { bullets: true });
  y = drawSectionHeading('Technical Source Notes', y + 2);
  y = drawTextLines(content.technicalSourceNotes, y);
  y = drawSectionHeading('Limitations', y + 2);
  y = drawTextLines(
    content.limitations.length > 0
      ? content.limitations
      : ['No additional limitations were supplied.'],
    y,
    { bullets: true }
  );
  y = drawSectionHeading('Advisory Disclaimer', y + 2);
  drawTextLines([content.disclaimer], y);

  const pageCount = report.getNumberOfPages();
  for (let page = 1; page <= pageCount; page += 1) {
    report.setPage(page);
    report.setDrawColor(...palette.lightGray);
    report.line(margin, pageHeight - 15, pageWidth - margin, pageHeight - 15);
    report.setFont('helvetica', 'normal');
    report.setFontSize(7.5);
    report.setTextColor(...palette.gray);
    report.text(
      'FarmLite | AI-assisted decision support',
      margin,
      pageHeight - 9
    );
    report.text(
      `Page ${page} of ${pageCount}`,
      pageWidth - margin,
      pageHeight - 9,
      { align: 'right' }
    );
  }

  return report;
};
