"use client";

import { useState } from "react";
import { CheckCircle, Circle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { Questionnaire, QuestionnaireQuestion } from "@/types";

interface QuestionnaireCardProps {
  questionnaire: Questionnaire;
  onSubmit: (answers: Record<string, string | string[] | boolean>) => Promise<void>;
}

export function QuestionnaireCard({
  questionnaire,
  onSubmit,
}: QuestionnaireCardProps) {
  const [answers, setAnswers] = useState<Record<string, string | string[] | boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (
    questionId: string,
    value: string | string[] | boolean
  ) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
    }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await onSubmit(answers);
      setSubmitted(true);
    } catch (err) {
      console.error("Failed to submit questionnaire:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isComplete = questionnaire.questions
    .filter((q) => q.required)
    .every((q) => {
      const answer = answers[q.id];
      if (typeof answer === "boolean") return true;
      if (Array.isArray(answer)) return answer.length > 0;
      return answer && answer.trim() !== "";
    });

  if (submitted) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
        <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
        <p className="text-green-700 font-medium">Questionnaire submitted!</p>
        <p className="text-sm text-green-600">
          Your answers have been recorded and will help refine the requirements.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-card border rounded-lg shadow-sm">
      <div className="p-4 border-b">
        <h3 className="font-semibold">{questionnaire.topic}</h3>
        <p className="text-sm text-muted-foreground">
          Please answer the following questions
        </p>
      </div>

      <div className="p-4 space-y-6">
        {questionnaire.questions.map((question, index) => (
          <QuestionField
            key={question.id}
            question={question}
            index={index}
            value={answers[question.id]}
            onChange={(value) => handleChange(question.id, value)}
          />
        ))}
      </div>

      <div className="p-4 border-t">
        <Button
          onClick={handleSubmit}
          disabled={!isComplete || isSubmitting}
          className="w-full"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Submitting...
            </>
          ) : (
            "Submit Answers"
          )}
        </Button>
      </div>
    </div>
  );
}

interface QuestionFieldProps {
  question: QuestionnaireQuestion;
  index: number;
  value: string | string[] | boolean | undefined;
  onChange: (value: string | string[] | boolean) => void;
}

function QuestionField({
  question,
  index,
  value,
  onChange,
}: QuestionFieldProps) {
  return (
    <div className="space-y-2">
      <label className="block">
        <span className="text-sm font-medium">
          {index + 1}. {question.question}
          {question.required && <span className="text-destructive ml-1">*</span>}
        </span>
      </label>

      {question.type === "text" && (
        <Input
          value={(value as string) || ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Type your answer..."
        />
      )}

      {question.type === "select" && question.options && (
        <div className="space-y-2">
          {question.options.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => onChange(option)}
              className={cn(
                "flex items-center gap-2 w-full p-2 rounded-md border text-left transition-colors",
                value === option
                  ? "border-primary bg-primary/5"
                  : "border-input hover:bg-accent"
              )}
            >
              {value === option ? (
                <CheckCircle className="w-4 h-4 text-primary" />
              ) : (
                <Circle className="w-4 h-4 text-muted-foreground" />
              )}
              {option}
            </button>
          ))}
        </div>
      )}

      {question.type === "multiselect" && question.options && (
        <div className="space-y-2">
          {question.options.map((option) => {
            const selected = Array.isArray(value) && value.includes(option);
            return (
              <button
                key={option}
                type="button"
                onClick={() => {
                  const current = (value as string[]) || [];
                  if (selected) {
                    onChange(current.filter((v) => v !== option));
                  } else {
                    onChange([...current, option]);
                  }
                }}
                className={cn(
                  "flex items-center gap-2 w-full p-2 rounded-md border text-left transition-colors",
                  selected
                    ? "border-primary bg-primary/5"
                    : "border-input hover:bg-accent"
                )}
              >
                {selected ? (
                  <CheckCircle className="w-4 h-4 text-primary" />
                ) : (
                  <Circle className="w-4 h-4 text-muted-foreground" />
                )}
                {option}
              </button>
            );
          })}
        </div>
      )}

      {question.type === "boolean" && (
        <div className="flex gap-4">
          <button
            type="button"
            onClick={() => onChange(true)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-md border transition-colors",
              value === true
                ? "border-primary bg-primary/5"
                : "border-input hover:bg-accent"
            )}
          >
            {value === true ? (
              <CheckCircle className="w-4 h-4 text-primary" />
            ) : (
              <Circle className="w-4 h-4 text-muted-foreground" />
            )}
            Yes
          </button>
          <button
            type="button"
            onClick={() => onChange(false)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-md border transition-colors",
              value === false
                ? "border-primary bg-primary/5"
                : "border-input hover:bg-accent"
            )}
          >
            {value === false ? (
              <CheckCircle className="w-4 h-4 text-primary" />
            ) : (
              <Circle className="w-4 h-4 text-muted-foreground" />
            )}
            No
          </button>
        </div>
      )}
    </div>
  );
}
