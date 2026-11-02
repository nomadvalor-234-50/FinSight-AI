
from pathlib import Path

import pandas as pd

try:
    from .categorization import categorize_transaction
except ImportError:  # Supports direct execution from the ai_engine directory.
    from categorization import categorize_transaction


def categorize_csv(
    input_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """Categorize a CSV without performing file I/O merely on module import."""
    module_directory = Path(__file__).resolve().parent
    source = Path(input_path) if input_path is not None else module_directory / "transactions.csv"
    destination = Path(output_path) if output_path is not None else module_directory / "categorized_transactions.csv"

    frame = pd.read_csv(source)
    frame["category"] = frame["description"].apply(categorize_transaction)
    frame.to_csv(destination, index=False)
    print("\nCategorized Transactions:\n")
    print(frame)
    print("\nCategorization completed!")
    print(f"Output saved successfully to {destination}")
    return frame


def main() -> None:
    categorize_csv()


if __name__ == "__main__":
    main()
