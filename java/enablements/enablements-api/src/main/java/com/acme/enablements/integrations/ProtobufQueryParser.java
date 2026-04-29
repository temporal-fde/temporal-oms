package com.acme.enablements.integrations;

import com.google.protobuf.Message;
import com.google.protobuf.util.JsonFormat;
import org.springframework.stereotype.Component;

import java.lang.reflect.Method;

@Component
public class ProtobufQueryParser {

    private final JsonFormat.Parser parser = JsonFormat.parser().ignoringUnknownFields();

    @SuppressWarnings("unchecked")
    public <T extends Message> T parse(String json, Class<T> messageClass) {
        try {
            Method newBuilder = messageClass.getMethod("newBuilder");
            Message.Builder builder = (Message.Builder) newBuilder.invoke(null);
            parser.merge(json == null || json.isBlank() ? "{}" : json, builder);
            return (T) builder.build();
        } catch (Exception e) {
            throw new IntegrationFixtureException(
                    IntegrationFixtureException.Code.BAD_REQUEST,
                    "Invalid protobuf JSON request for " + messageClass.getSimpleName() + ": " + e.getMessage());
        }
    }
}
