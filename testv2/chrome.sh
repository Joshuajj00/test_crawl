#!/bin/bash

echo "Detected Chrome version: $(google-chrome --version)"

# 최신 안정 버전의 ChromeDriver 확인
CHROMEDRIVER_VERSION=$(curl -sS "https://chromedriver.storage.googleapis.com/LATEST_RELEASE")

if [ -z "$CHROMEDRIVER_VERSION" ]; then
    echo "Error: Unable to find the latest ChromeDriver version."
    exit 1
fi

echo "Using latest stable ChromeDriver version: $CHROMEDRIVER_VERSION"

# ChromeDriver 다운로드
wget -O chromedriver_linux64.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"

if [ $? -ne 0 ]; then
    echo "Error: Failed to download ChromeDriver."
    exit 1
fi

# 압축 해제
unzip chromedriver_linux64.zip

if [ ! -f "chromedriver" ]; then
    echo "Error: ChromeDriver executable not found after extraction."
    exit 1
fi

# ChromeDriver 이동 및 권한 설정
sudo mv chromedriver /usr/local/bin/chromedriver
sudo chown root:root /usr/local/bin/chromedriver
sudo chmod +x /usr/local/bin/chromedriver

# 정리
rm chromedriver_linux64.zip

echo "ChromeDriver ${CHROMEDRIVER_VERSION} has been successfully installed."

# 설치 확인
INSTALLED_VERSION=$(/usr/local/bin/chromedriver --version | awk '{print $2}')
echo "Installed ChromeDriver version: $INSTALLED_VERSION"
