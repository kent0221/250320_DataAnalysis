# TikTok Data Analytics Tool - Application Description

## Overview

A personal-use command-line tool for analyzing TikTok video statistics.

## Purpose

- Fetch and analyze public video data
- Track video performance metrics
- Generate CSV reports for personal analysis

## Technical Details

- Built with Python 3.8
- Uses official TikTok API
- Local MySQL database storage
- AES-256 encryption for data protection

## Data Collection

- Public video statistics only
- No personal user data stored
- Automatic data deletion after 30 days

## API Usage

- Respects rate limits (600 requests/minute)
- Required scopes:
  - video.list
  - video.query
  - user.info.basic

## Security Measures

- Encrypted local storage
- No third-party data sharing
- Secure credential management
