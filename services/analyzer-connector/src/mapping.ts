import { ParsedResult } from "./adapter.js";

export interface TestMappingConfig {
  [machineTestCode: string]: {
    standardTestCode: string;
    testName?: string;
    factor?: number; // scaling factor if needed
    allowedRange?: { min: number; max: number };
  };
}

export interface MappedResult {
  sampleId: string;
  standardTestCode: string;
  machineTestCode: string;
  value: number | string;
  numericValue?: number;
  units?: string;
  flags?: string;
  isValid: boolean;
  validationError?: string;
  timestamp: string;
  rawMessageId: string;
}

export class AnalyzerMapper {
  private mappingConfig: TestMappingConfig;

  constructor(mappingConfig: TestMappingConfig = {}) {
    this.mappingConfig = mappingConfig;
  }

  setMapping(config: TestMappingConfig) {
    this.mappingConfig = { ...this.mappingConfig, ...config };
  }

  mapResult(parsed: ParsedResult): MappedResult {
    const mapping = this.mappingConfig[parsed.testCode];
    const standardTestCode = mapping ? mapping.standardTestCode : parsed.testCode;
    
    let numericValue: number | undefined = undefined;
    let isValid = true;
    let validationError: string | undefined = undefined;

    const parsedNum = parseFloat(parsed.value);
    if (!isNaN(parsedNum)) {
      numericValue = parsedNum;
      if (mapping && mapping.factor) {
        numericValue = parsedNum * mapping.factor;
      }
      if (mapping && mapping.allowedRange) {
        if (numericValue < mapping.allowedRange.min || numericValue > mapping.allowedRange.max) {
          // Out of range flags can be marked or flagged, but value is valid format.
          // If out of physical bounds e.g. negative where impossible, mark invalid.
          if (numericValue < 0 && mapping.allowedRange.min >= 0) {
            isValid = false;
            validationError = `Value ${numericValue} is below physically possible minimum ${mapping.allowedRange.min}`;
          }
        }
      }
    } else if (!parsed.value || parsed.value.trim() === "") {
      isValid = false;
      validationError = "Empty test result value";
    }

    return {
      sampleId: parsed.sampleId,
      standardTestCode,
      machineTestCode: parsed.testCode,
      value: numericValue !== undefined ? numericValue : parsed.value,
      numericValue,
      units: parsed.units,
      flags: parsed.flags,
      isValid,
      validationError,
      timestamp: parsed.timestamp,
      rawMessageId: parsed.rawMessageId,
    };
  }

  mapBatch(parsedResults: ParsedResult[]): MappedResult[] {
    return parsedResults.map((p) => this.mapResult(p));
  }
}
