import os
import importlib
import logging

logger = logging.getLogger(__name__)


def load_all_features(application, folder="features"):
    """
    Auto load all features from features folder.
    Any file with register(application) will be loaded automatically.
    """

    if not os.path.exists(folder):
        print("❌ features folder not found")
        return

    for file in os.listdir(folder):

        # تجاهل الملفات غير python
        if not file.endswith(".py"):
            continue

        # تجاهل __init__
        if file.startswith("__"):
            continue

        module_name = file[:-3]  # remove .py

        try:
            module_path = f"{folder}.{module_name}"

            module = importlib.import_module(module_path)

            # لو الملف فيه register
            if hasattr(module, "register"):
                module.register(application)
                print(f"✅ Loaded feature: {module_name}")
                logger.info(f"Loaded feature: {module_name}")

            else:
                print(f"⚠️ {module_name} has no register()")

        except Exception as e:
            print(f"❌ Failed loading {module_name}: {e}")
            logger.error(f"Feature load error {module_name}: {e}")
