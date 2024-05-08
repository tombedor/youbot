# import os
# from pyexpat import model
# from datasets import Dataset
# from transformers import AutoTokenizer

# from youbot.experiments.q_and_a_dataset_generation import get_data

# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, default_data_collator, get_linear_schedule_with_warmup

# # from peft import get_peft_model
# from peft import PrefixTuningConfig
# from peft import TaskType
# from torch.utils.data import DataLoader
# from tqdm import tqdm
# import torch
# import os

# from peft import get_peft_model

# model_name_or_path = "t5-large"
# batch_size = 8
# max_length = 128
# lr = 1e-2
# num_epochs = 1
# batch_size = 8
# device = "cpu"

# dataset = Dataset.from_list(get_data())
# dataset = dataset.train_test_split(test_size=0.1)

# for q_and_a in get_data():
#     print(q_and_a["PROMPT"], q_and_a["LABEL"])


# os.environ["TOKENIZERS_PARALLELISM"] = "false"
# os.environ["CUDA_VISIBLE_DEVICES"] = "3"
# tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
# # tokenizer.pad_token = tokenizer.eos_token

# # padding token for mixtral model


# def preprocess_function(examples):
#     inputs = examples["PROMPT"]
#     targets = examples["LABEL"]
#     model_inputs = tokenizer(inputs, max_length=128, padding="max_length", truncation=True, return_tensors="pt")
#     labels = tokenizer(targets, max_length=2, padding="max_length", truncation=True, return_tensors="pt")
#     labels = labels["input_ids"]
#     labels[labels == tokenizer.pad_token_id] = -100
#     model_inputs["labels"] = labels
#     return model_inputs


# processed_datasets = dataset.map(
#     preprocess_function,
#     batched=True,
#     num_proc=1,
#     # remove_columns=dataset.column_names,
#     load_from_cache_file=False,
#     desc="Running tokenizer on dataset",
# )

# train_dataset = processed_datasets["train"]
# eval_dataset = processed_datasets["test"]

# train_dataloader = DataLoader(train_dataset, shuffle=True, collate_fn=default_data_collator, batch_size=batch_size, pin_memory=True)
# eval_dataloader = DataLoader(eval_dataset, collate_fn=default_data_collator, batch_size=batch_size, pin_memory=True)


# peft_config = PrefixTuningConfig(task_type=TaskType.SEQ_2_SEQ_LM, inference_mode=False, num_virtual_tokens=20)

# model = AutoModelForSeq2SeqLM.from_pretrained(model_name_or_path)
# model = get_peft_model(model, peft_config)
# model.print_trainable_parameters()
# optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
# lr_scheduler = get_linear_schedule_with_warmup(
#     optimizer=optimizer,
#     num_warmup_steps=0,
#     num_training_steps=(len(train_dataloader) * num_epochs),
# )


# model = model.to(device)

# for epoch in range(num_epochs):
#     model.train()
#     total_loss = 0
#     for step, batch in enumerate(tqdm(train_dataloader)):
#         batch = {k: v.to(device) for k, v in batch.items()}
#         outputs = model(**batch)
#         loss = outputs.loss
#         total_loss += loss.detach().float()
#         loss.backward()
#         optimizer.step()
#         lr_scheduler.step()
#         optimizer.zero_grad()

#     model.eval()
#     eval_loss = 0
#     eval_preds = []
#     for step, batch in enumerate(tqdm(eval_dataloader)):
#         batch = {k: v.to(device) for k, v in batch.items()}
#         with torch.no_grad():
#             outputs = model(**batch)
#         loss = outputs.loss
#         eval_loss += loss.detach().float()
#         eval_preds.extend(tokenizer.batch_decode(torch.argmax(outputs.logits, -1).detach().cpu().numpy(), skip_special_tokens=True))

#     eval_epoch_loss = eval_loss / len(eval_dataloader)
#     eval_ppl = torch.exp(eval_epoch_loss)
#     train_epoch_loss = total_loss / len(train_dataloader)
#     train_ppl = torch.exp(train_epoch_loss)
#     print(f"{epoch=}: {train_ppl=} {train_epoch_loss=} {eval_ppl=} {eval_epoch_loss=}")

# correct = 0
# total = 0
# for pred, true in zip(eval_preds, dataset["test"]["LABEL"]):
#     print(f"PREDICTED = {pred}")
#     print(f"TRUE = {true}")
#     if pred.strip() == true.strip():
#         correct += 1
#     total += 1
# accuracy = correct / total * 100
# print(f"{accuracy=} % on the evaluation dataset")
# print(f"{eval_preds[:10]=}")
# print(f"{dataset['test']['PROMPT'][:10]=}")
# # "accuracy=97.3568281938326 % on the evaluation dataset"
# # "eval_preds[:10]=['neutral', 'positive', 'neutral', 'positive', 'neutral', 'negative', 'negative', 'neutral', 'neutral', 'neutral']"
# # "dataset['validation']['text_label'][:10]=['neutral', 'positive', 'neutral', 'positive', 'neutral', 'negative', 'negative', 'neutral', 'neutral', 'neutral']"

# # Dataset.from_list(ds['train'])


# # generate test data (what format)

# # peft with prefix tuning on mixtral
