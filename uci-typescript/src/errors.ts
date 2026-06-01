/**
 * UCI Error Hierarchy
 * All exceptions raised by the UCI stack.
 */

export class UCIError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "UCIError";
  }
}

export class UCIManifestError extends UCIError {
  constructor(message: string) {
    super(message);
    this.name = "UCIManifestError";
  }
}

export class UCIValidationError extends UCIError {
  constructor(message: string) {
    super(message);
    this.name = "UCIValidationError";
  }
}

export class UCIGovernanceError extends UCIError {
  public readonly outcome: string;
  public readonly reason: string;
  constructor(message: string, outcome = "deny", reason = "") {
    super(message);
    this.name    = "UCIGovernanceError";
    this.outcome = outcome;
    this.reason  = reason;
  }
}

export class UCITrustError extends UCIError {
  public readonly currentState: string;
  public readonly requiredState: string;
  constructor(message: string, currentState = "", requiredState = "") {
    super(message);
    this.name         = "UCITrustError";
    this.currentState = currentState;
    this.requiredState= requiredState;
  }
}

export class UCIHandshakeError extends UCIError {
  public readonly stage: string;
  constructor(message: string, stage = "") {
    super(message);
    this.name  = "UCIHandshakeError";
    this.stage = stage;
  }
}

export class UCIInvocationError extends UCIError {
  public readonly actionId: string;
  public readonly errorCode: string;
  constructor(message: string, actionId = "", errorCode = "") {
    super(message);
    this.name      = "UCIInvocationError";
    this.actionId  = actionId;
    this.errorCode = errorCode;
  }
}

export class UCIRegistryError extends UCIError {
  constructor(message: string) {
    super(message);
    this.name = "UCIRegistryError";
  }
}
