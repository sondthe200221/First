USE DictionaryDB;
GO

ALTER PROCEDURE sp_InsertDictionaryJson
    @json NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @word NVARCHAR(100);
    
    -- Lấy từ từ JSON
    SELECT TOP 1 @word = word FROM OPENJSON(@json) WITH (word NVARCHAR(100) '$.word');

    -- Nếu từ này chưa có thì mới Insert để tránh lỗi UNIQUE KEY
    IF @word IS NOT NULL AND NOT EXISTS (SELECT 1 FROM Words WHERE WordText = @word)
    BEGIN
        INSERT INTO Words (WordText, Phonetic)
        SELECT TOP 1 word, phonetic FROM OPENJSON(@json) WITH (word NVARCHAR(100) '$.word', phonetic NVARCHAR(100) '$.phonetic');
        
        DECLARE @wid INT = SCOPE_IDENTITY();

        -- Insert định nghĩa
        INSERT INTO Definitions (WordID, PartOfSpeech, DefinitionText)
        SELECT @wid, partOfSpeech, def
        FROM OPENJSON(@json, '$[0].meanings') 
        WITH (partOfSpeech NVARCHAR(50) '$.partOfSpeech', definitions NVARCHAR(MAX) '$.definitions' AS JSON)
        CROSS APPLY OPENJSON(definitions) WITH (def NVARCHAR(MAX) '$.definition');
    END
END
GO