import gradio as gr
from generate_notes_from_doc import main, sync_vdb_wit_vault_recursive
from edit_vector_db import get_all_used_filenames, delete_selected_file
import ollama
from chat import gr_chat, gr_chat_graph
from obsidian_graph.parser import parse_vault


def process_inputs(
    filter_on_headers,
    MAX_LLM_RETRY,
    sleep_time,
    source,
    vault_name,
    provider,
    tags,
    restrict_to_vault,
    MAX_COSINE_DISTANCE,
    model_name,
):

    try:
        print(
            "INPUTS: ",
            filter_on_headers,
            MAX_LLM_RETRY,
            sleep_time,
            source,
            vault_name,
            provider,
            model_name,
            tags,
            restrict_to_vault,
            MAX_COSINE_DISTANCE,
        )

        main(
            source=source,
            vault_name=vault_name,
            filter_on_headers=filter_on_headers,
            provider=provider,
            model_name=model_name,
            MAX_LLM_RETRY=MAX_LLM_RETRY,
            sleep_time=sleep_time,
            tags=tags,
            restrict_to_vault=restrict_to_vault,
            MAX_COSINE_DISTANCE=MAX_COSINE_DISTANCE,
        )

        return f"Processed with {provider} and model {model_name}\nTags: {tags}"
    except Exception as e:
        print(f"ERROR: {e}")
        return f"ERROR: {e}"




with gr.Blocks() as demo:
    gr.Markdown("# Obsidian Assist")

    # Shared: Provider and Model Controls
    provider = gr.Dropdown(
        label="Provider", choices=["gemini", "huggingface", "ollama"], value="gemini"
    )

    model_input_mode = gr.Radio(
        label="Select Model Input Type",
        choices=["Dropdown", "Textbox"],
        value="Dropdown",
        interactive=True,
    )

    model_dropdown = gr.Dropdown(
        label="Model Name (Dropdown)",
        choices=[
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-1.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
        ],
        value="gemini-2.0-flash",
        visible=True,
    )

    model_textbox = gr.Textbox(
        label="Model Name (Textbox)", placeholder="Enter model name", visible=False
    )

    # Toggle model dropdown/textbox visibility
    def toggle_model_input(input_type):
        if input_type == "Dropdown":
            return gr.update(visible=True), gr.update(visible=False)
        else:
            return gr.update(visible=False), gr.update(visible=True)

    model_input_mode.change(
        fn=toggle_model_input,
        inputs=model_input_mode,
        outputs=[model_dropdown, model_textbox],
    )

    # Update model dropdown based on provider
    def update_model_choices(selected_provider):
        if selected_provider == "gemini":
            return gr.update(
                choices=[
                    "gemini-1.5-flash",
                    "gemini-1.5-flash-8b",
                    "gemini-1.5-pro",
                    "gemini-2.0-flash",
                    "gemini-2.0-flash-lite",
                ],
                value="gemini-2.0-flash",
            )
        elif selected_provider == "huggingface":
            return gr.update(
                choices=["Qwen/Qwen2.5-72B-Instruct"], value="Qwen/Qwen2.5-72B-Instruct"
            )
        elif selected_provider == "ollama":
            all_ollama_models = [i.model for i in ollama.list().models]
            return gr.update(
                choices=all_ollama_models,
                value=all_ollama_models[0] if all_ollama_models else "",
            )
        else:
            return gr.update(choices=[], value=None)

    provider.change(fn=update_model_choices, inputs=provider, outputs=model_dropdown)

    MAX_COSINE_DISTANCE = gr.Slider(
        label="Max Cosine Distance",
        info="0 indicates identical vectors and 2 indicates opposite vectors",
        minimum=0,
        maximum=2,
        step=0.01,
        value=0.3,
    )

    with gr.Tab("Generate Notes"):

        # Inputs for filtering and retries
        filter_on_headers = gr.Checkbox(
            label="Filter on Headers",
            info="If True, chunks with header simlar to those in cleaning_utils.headers_to_skip(like References, Index, Footnotes etc) will be skipped.",
            value=True,
        )

        restrict_to_vault = gr.Checkbox(
            label="Restrict Links and context to Vault", value=False
        )

        MAX_LLM_RETRY = gr.Slider(
            label="Max LLM Retry",
            info="Number of retries on a paticular chunk in case of an error. Higher values might lead to more API calls.",
            minimum=1,
            maximum=10,
            step=1,
            value=3,
        )

        sleep_time = gr.Slider(
            label="Sleep Time (seconds)",
            info="Cool down time between LLM API calls.",
            minimum=1,
            maximum=60,
            step=1,
            value=5,
        )

        # File and directory inputs
        source = gr.Textbox(
            label="Source File Path", placeholder="Enter the local path to a file"
        )
        vault_name = gr.Textbox(
            label="Vault Directory Path",
            placeholder="Enter the local path to a directory",
        )

        # Tags field
        tags = gr.Textbox(
            label="Tags",
            placeholder="Enter tags separated by # (e.g., #tag1 #tag2). tags are also generated based on content in the backend.",
        )

        # Submit button
        submit_button = gr.Button("Generate Notes")

        # Output display
        output = gr.Textbox(label="Status")

        def process_model_name(model_input_type, model_dropdown, model_textbox):
            return model_dropdown if model_input_type == "Dropdown" else model_textbox

        submit_button.click(
            fn=lambda *inputs: process_inputs(
                *inputs[:-3], process_model_name(*inputs[-3:])
            ),
            inputs=[
                filter_on_headers,
                MAX_LLM_RETRY,
                sleep_time,
                source,
                vault_name,
                provider,
                tags,
                restrict_to_vault,
                MAX_COSINE_DISTANCE,
                model_input_mode,
                model_dropdown,
                model_textbox,
            ],
            outputs=output,
        )

    with gr.Tab("Delete document chunks from DB"):

        ## vdb_notes_collection_name will automatically sync with the vault, hence no need to do it here

        available_files = gr.Dropdown(
            label="Available Files",
            choices=get_all_used_filenames(),
            value="",
            visible=True,
        )

        delete_button = gr.Button("Delete File")

        # Output display
        output_del = gr.Textbox(label="Status")

        ## delete all with that file name

        delete_button.click(
            fn=delete_selected_file, inputs=available_files, outputs=output_del
        )

    with gr.Tab("Sync Notes Vault with DB"):
        vault_path_sync = gr.Textbox(
            label="Vault Path",
            placeholder="Enter Vault directory path",
        )

        sync_btn = gr.Button("Sync Button")

        # Output display
        output_sync = gr.Textbox(label="Status")

        sync_btn.click(
            fn=sync_vdb_wit_vault_recursive, inputs=vault_path_sync, outputs=output_sync
        )
    with gr.Tab("Chat"):
        with gr.Tab("Simple RAG"):
            gr.ChatInterface(
                fn=lambda *inputs: gr_chat(
                    message=inputs[0],
                    history=inputs[1],
                    provider=inputs[2],
                    model_name=process_model_name(*inputs[-3:]),
                    MAX_COSINE_DISTANCE=inputs[3],
                ),
                title="Notes chat",
                description="Ask me anything!",
                theme="soft",
                type="messages",
                additional_inputs=[
                    provider,
                    MAX_COSINE_DISTANCE,
                    model_input_mode,
                    model_dropdown,
                    model_textbox,
                ],
            )
        with gr.Tab("Graph Based Context"):

            def update_nodes_dropdown_with_vault_files(notes_vault_path):
                ## update option according to vault
                notes = parse_vault(notes_vault_path)
                notes_keys = list(notes.keys())

                dropdown_options = ["None"]
                dropdown_options.extend(notes_keys)

                print(dropdown_options)

                return [
                    notes,
                    gr.update(
                        choices=dropdown_options,
                        value=dropdown_options[0],
                        visible=True,
                    ),
                    gr.update(
                        choices=dropdown_options,
                        value=dropdown_options[0],
                        visible=True,
                    ),
                ]

            notes_vault_path = gr.Textbox(
                label="Vault Path",
                placeholder="Enter Vault directory path whose graph should be used",
            )

            notes_sync_init_btn = gr.Button("Initialize")

            hops = gr.Slider(
                label="Hops",
                info="Number of hops ancestors/children from the chosen node. Not used if End is selected",
                minimum=1,
                maximum=10,
                step=1,
                value=1,
            )

            start_notes_dropdown = gr.Dropdown(
                label="Start",
                choices=["None"],
                value="None",
                interactive=True,
                visible=False,
            )

            end_notes_dropdown = gr.Dropdown(
                label="End",
                info="If selected, the shortest path between Start and End will be included in context.",
                choices=["None"],
                value="None",
                interactive=True,
                visible=False,
            )

            notes = gr.State({})

            notes_sync_init_btn.click(
                fn=update_nodes_dropdown_with_vault_files,
                inputs=notes_vault_path,
                outputs=[notes, start_notes_dropdown, end_notes_dropdown],
            )

            graph_chat = gr.ChatInterface(
                fn=lambda *inputs: gr_chat_graph(
                    message=inputs[0],
                    history=inputs[1],
                    provider=inputs[2],
                    model_name=process_model_name(*inputs[-3:]),
                    MAX_COSINE_DISTANCE=inputs[3],
                    start=inputs[4],
                    end=inputs[5],
                    notes=inputs[6],
                    hops=inputs[7],
                ),
                title="Graph chat",
                description="Intialize Vault and then ask me anything!",
                theme="soft",
                type="messages",
                additional_inputs=[
                    provider,
                    MAX_COSINE_DISTANCE,
                    start_notes_dropdown,
                    end_notes_dropdown,
                    notes,
                    hops,
                    model_input_mode,
                    model_dropdown,
                    model_textbox,
                ],
            )


demo.launch()
