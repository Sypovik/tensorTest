#!/bin/bash

# Цвета ANSI
COLOR_RESET="\e[0m"
COLOR_RED="\e[31m"
COLOR_GREEN="\e[32m"
COLOR_YELLOW="\e[33m"
COLOR_BLUE="\e[34m"
COLOR_CYAN="\e[36m"
COLOR_BOLD="\e[1m"

log() {
    echo -e "${COLOR_CYAN}[$(date '+%T')]${COLOR_RESET} $*"
}

bold() {
    echo -e "${COLOR_BOLD}$*${COLOR_RESET}"
}

log_info() {
    log "${COLOR_BLUE}[INFO] ${COLOR_RESET} $*"
}

log_success() {
    log "${COLOR_GREEN}[OK]   ${COLOR_RESET} $*"
}

log_warn() {
    log "${COLOR_YELLOW}[WARN] ${COLOR_RESET} $*"
}

log_error() {
    log "${COLOR_RED}[ERROR]${COLOR_RESET} $*"
}
