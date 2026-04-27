import pathlib


def test_uses_session_state():
    src = pathlib.Path(__file__).parent.joinpath("buggy.py").read_text()
    assert "st.session_state" in src, (
        "secret must be stored in st.session_state so it survives Streamlit reruns"
    )
