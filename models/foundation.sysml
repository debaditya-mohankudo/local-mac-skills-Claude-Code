package Foundation {
    doc
    /*
     * Shared provenance metadata used by every package in this model so a
     * model's staleness against the code it describes is checkable, not
     * assumed. See mbse-claude-hooks-model / task-framework for the same
     * convention.
     */

    metadata def ModelProvenance {
        doc
        /*
         * Stamped per-package: the last commit that touched the source
         * paths that package's doc comments cite, not the commit that adds
         * the .sysml file itself.
         */
        attribute derivedFromCommit : String;
        attribute derivedAt : String;
        attribute modelledPaths : String[0..*];
    }

    @ModelProvenance {
        derivedFromCommit = "2cadbff8234728e4e7cc189a8662e48feefed9a1";
        derivedAt = "2026-10-27";
        modelledPaths = (
            "tests/test_model_provenance.py"
        );
    }
}
