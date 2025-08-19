install:
	. .venv/bin/activate; pip install -Ur requirements.txt

activate:
	. .venv/bin/activate

install_venv:
	python -m venv .venv

formatter:
	. .venv/bin/activate; command black --line-length 125 .

check_format:
	. .venv/bin/activate; command black --line-length 125 . --check

automatic_shutdown:
	. .venv/bin/activate; command python src/ml_cloud_connector/use_cases/AutomaticShutDownUseCase.py

tag:
	#!/bin/bash
	# Get current date
	CURRENT_DATE=$(date +%Y.%-m.%-d)
	echo "Current date: $CURRENT_DATE"

	# Get the latest tag that matches today's date pattern
	LATEST_TAG=$(git tag --list "${CURRENT_DATE}.*" --sort=-version:refname | head -n1)

	if [ -z "$LATEST_TAG" ]; then
		# No tag for today, start with revision 1
		REVISION=1
	else
		# Extract revision number and increment
		REVISION=$(echo $LATEST_TAG | cut -d. -f4)
		REVISION=$((REVISION + 1))
	fi

	NEW_TAG="${CURRENT_DATE}.${REVISION}"
	echo "Creating new tag: $NEW_TAG"
	git tag $NEW_TAG
	git push --tag