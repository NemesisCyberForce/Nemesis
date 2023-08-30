# Standard Libraries
import os
import urllib

# 3rd Party Libraries
import streamlit as st
import templates
import utils
from annotated_text import annotated_text, annotation

utils.header()

page_size = int(os.environ["PAGE_SIZE"])
NEMESIS_HTTP_SERVER = os.environ.get("NEMESIS_HTTP_SERVER")

if st.session_state["authentication_status"]:
    with st.expander("About NoseyParker Search"):
        st.markdown(
            """
        This page lists all files that have NoseyParker results.

        Results are grouped by each file with matching results.
        """
        )

    # default values
    if "np_page" not in st.session_state:
        st.session_state.np_page = 1

    # get parameters in url
    para = st.experimental_get_query_params()
    if "np_page" in para:
        st.experimental_set_query_params()
        st.session_state.np_page = int(para["np_page"][0])

    from_i = (st.session_state.np_page - 1) * page_size
    results = utils.elastic_np_search(from_i, page_size)

    if results != {}:
        total_hits = results["hits"]["total"]["value"]
        num_results = len(results["hits"]["hits"])

        if total_hits > 0:
            st.write(templates.number_of_results(total_hits, results["took"] / 1000), unsafe_allow_html=True)

            for i in range(num_results):
                # http://172.16.111.187:8080/api/download/bd48a461-a1a5-42a9-8e87-07ce62408303?name=nosey_parker_google.config
                object_id = results["hits"]["hits"][i]["_source"]["objectId"]
                file_name = results["hits"]["hits"][i]["_source"]["name"]
                download_url = f"{NEMESIS_HTTP_SERVER}/api/download/{object_id}?name={file_name}"
                kibana_link = f"{NEMESIS_HTTP_SERVER}/kibana/app/discover#/?_a=(filters:!((query:(match_phrase:(objectId:'{object_id}')))),index:'26360ae8-a518-4dac-b499-ef682d3f6bac')&_g=(time:(from:now-1y%2Fd,to:now))"
                path = results["hits"]["hits"][i]["_source"]["path"]
                sha1 = results["hits"]["hits"][i]["_source"]["hashes"]["sha1"]
                source = ""
                if "metadata" in results["hits"]["hits"][i]["_source"] and "source" in results["hits"]["hits"][i]["_source"]["metadata"]:
                    source = results["hits"]["hits"][i]["_source"]["metadata"]["source"]

                if source:
                    expander_text = f"{source} : **{path}** (SHA1: {sha1})"
                else:
                    expander_text = f"**{path}** (SHA1: {sha1})"

                with st.expander(expander_text):
                    st.write(
                        f"""
                        <a href="{kibana_link}">
                            File in Kibana
                        </a>
                        &nbsp; &nbsp; &nbsp;
                        <a href="{download_url}">
                            Download File
                        </a>
                    """,
                        unsafe_allow_html=True,
                    )
                    st.divider()
                    for ruleMatch in results["hits"]["hits"][i]["_source"]["noseyparker"]["ruleMatches"]:
                        for match in ruleMatch["matches"]:
                            if "matching" in match["snippet"]:
                                rule_name = match["ruleName"]

                                if "before" in match["snippet"]:
                                    before = match["snippet"]["before"].replace("\n\t", " ")
                                else:
                                    before = ""

                                matching = match["snippet"]["matching"]

                                if "after" in match["snippet"]:
                                    after = match["snippet"]["after"].replace("\n\t", " ")
                                else:
                                    after = ""

                                st.write(f"<b>Rule</b>: {rule_name}", unsafe_allow_html=True)
                                annotated_text(annotation(before, "context", color="#8ef"), annotation(matching, "match"), annotation(after, "context", color="#8ef"))
                                st.divider()

            # pagination
            if total_hits > page_size:
                total_pages = (total_hits + page_size - 1) // page_size
                pagination_html = templates.np_pagination(total_pages, st.session_state.np_page)
                st.write(pagination_html, unsafe_allow_html=True)
        else:
            st.write(templates.no_result_html(), unsafe_allow_html=True)
