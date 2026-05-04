export const VALID_MATERIALS = [
  "Beton | Mörtel",
  "Beton | Spannbeton",
  "Beton | Stahlbeton",
  "Beton | Schleuderbeton",
  "Mauerwerk | Kalksandstein",
  "Mauerwerk | Betonstein",
  "Mauerwerk | Ziegelstein",
  "Metall | legierten Stahl",
  "Metall | unlegierten Stahl",
  "Steine | Geotextil",
  "Steine | Kies",
] as const;

export const VALID_DAMAGE_TYPES = [
  "Beton | Feuchte Stelle",
  "Beton | Kantenabbruch",
  "Beton | Rostfahnen",
  "Risse | Gerissen",
  "Risse | Diagonal (nass)",
  "Risse | Längsriss (trocken)",
  "Formänderung | Angrenzend",
  "Formänderung | Abgesackt",
  "Allgemein | Verformt",
  "Allgemein | Abgerissen",
  "Allgemein | Verschlissen/locker",
  "Mauerwerk | Verwitterung",
  "Bewehrung | Lochkorrosion",
  "Maßangabe | Zu groß",
  "Maßangabe | Zu klein",
  "Stahl | Verrostet",
] as const;

export const VALID_OBJECT_PART_CATEGORIES = [
  "Ausstattung",
  "Fugen",
  "Festmachereinrichtungen",
  "Sonstiges",
  "Dichtungen",
  "Stahlkonstruktion",
] as const;

export const VALID_MAIN_COMPONENT_CATEGORIES = [
  "Konstruktion",
  "Ausstattung",
  "Sonstiges",
  "Stahlkonstruktion",
] as const;

export const VALID_STATUSES = ["Damage", "Suspicion", "Fixed", "Incorrectly detected"] as const;
export const VALID_QUANTITIES = ["general", "isolated", "one piece"] as const;
export const VALID_CLASSES = ["1", "2", "3", "4"] as const;
export const VALID_OPTIONAL_REMARKS = ["Engage external institute", "See last monitoring"] as const;
export const YES_NO_OPTIONS = ["Yes", "No"] as const;

export interface FieldConfig {
  editor: "select" | "number" | "text";
  options?: readonly string[];
  helper: string | null;
}

export const FIELD_CONFIG: Record<string, FieldConfig> = {
  Status: {
    editor: "select",
    options: VALID_STATUSES,
    helper: "Choose a valid InfraCloud status.",
  },
  "Damage Type": {
    editor: "select",
    options: VALID_DAMAGE_TYPES,
    helper: "Select an allowed WSV damage type.",
  },
  Class: {
    editor: "select",
    options: VALID_CLASSES,
    helper: "Use the valid class values 1-4.",
  },
  Quantity: {
    editor: "select",
    options: VALID_QUANTITIES,
    helper: "Use the supported quantity values.",
  },
  Material: {
    editor: "select",
    options: VALID_MATERIALS,
    helper: "Select an allowed WSV material value.",
  },
  "Object Part Category": {
    editor: "select",
    options: VALID_OBJECT_PART_CATEGORIES,
    helper: "Choose from the supported object part categories.",
  },
  "Main Component Category": {
    editor: "select",
    options: VALID_MAIN_COMPONENT_CATEGORIES,
    helper: "Choose from the supported main component categories.",
  },
  "Optional remark": {
    editor: "select",
    options: VALID_OPTIONAL_REMARKS,
    helper: "Use one of the predefined optional remarks.",
  },
  Closed: {
    editor: "select",
    options: YES_NO_OPTIONS,
    helper: "Use Yes or No.",
  },
  "Danger to life and health": {
    editor: "select",
    options: YES_NO_OPTIONS,
    helper: "Use Yes or No.",
  },
  "Immediate measures": {
    editor: "select",
    options: YES_NO_OPTIONS,
    helper: "Use Yes or No.",
  },
  "Current: Danger to life and limb": {
    editor: "select",
    options: YES_NO_OPTIONS,
    helper: "Use Yes or No.",
  },
  Length: {
    editor: "number",
    helper: "Numeric value only.",
  },
  Width: {
    editor: "number",
    helper: "Numeric value only.",
  },
  Depth: {
    editor: "number",
    helper: "Numeric value only.",
  },
  "Estimated Remaining Cross Section": {
    editor: "number",
    helper: "Numeric value only.",
  },
};

export function getFieldConfig(field: string): FieldConfig {
  return FIELD_CONFIG[field] || { editor: "text", helper: null };
}
