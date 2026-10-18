# Run the testthat suite: Rscript tests/R/run_tests.R (from the repo root
# or anywhere; paths resolve from this file). Non-zero exit on any failure.
args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
root <- dirname(dirname(here))
suppressPackageStartupMessages(library(testthat))
source(file.path(root, "R", "functions.R"))
env <- new.env()
env$root <- root
res <- test_file(file.path(here, "test_functions.R"), env = env, reporter = "summary", stop_on_failure = TRUE)
df <- as.data.frame(res)
if (nrow(df) == 0) stop("no tests ran")
cat(sprintf("\n%d tests, %d failed\n", nrow(df), sum(df$failed)))
