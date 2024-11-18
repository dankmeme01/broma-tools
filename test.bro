// Let's pretend this is a license clause
// Boring ass shit

// kill me
//
//

// agafdbdsgnsgn
/* And
a multiline
comment

*/
/* great*/
// wow


[[link(android)]]
class MyClass : Base1, Base2 {
    virtual void onClosePopup(UploadActionPopup*) { // hi
        log::debug("test");
        if (true == false) {
            log::warn("this is vile");
        }
    }

    void multiLineSig(
        int x,
        float y,
        CCObject* z
    ) = win 0x123; // comment!

    void multiLineSig2(
        float z
    ) {
        return;
    }

    /*
    big
    fat
    multiline
    comment
    */

    /* Simpler comment */
    /*Somewhat simple
     comment*/

    // comment
    [[test(a),
    test(b)]]
    static callback virtual void woah(gd::map<gd::string, gd::string const&> const& insane) = win inline, mac 0x3 {
        // another one
        log::debug("holy shit");
    }

    void * m_myMember; // inline comment on a member
    PAD = win 0x3, android32 0x4;
    void* m_anotherMemberWithCorrectAsterisk;

    win, mac {
        bool m_platformSpecific;
    }

    [[
        missing(android),
        not_missing(windows)
    ]]
    int m_memberWithAttr;

    uint8_t test[4];
}

